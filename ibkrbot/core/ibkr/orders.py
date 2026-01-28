from __future__ import annotations
from typing import Tuple
from ibapi.order import Order


class BracketOrderError(Exception):
    """Raised when bracket order parameters are invalid."""
    pass


def validate_bracket_prices(action: str, entry: float, stop: float, take: float) -> None:
    """
    Validate that bracket order prices are logically consistent.

    For BUY orders: stop < entry < take
    For SELL orders: take < entry < stop

    Args:
        action: "BUY" or "SELL"
        entry: Entry limit price
        stop: Stop loss price
        take: Take profit price

    Raises:
        BracketOrderError: If prices are not logically consistent
    """
    if entry <= 0 or stop <= 0 or take <= 0:
        raise BracketOrderError("All prices must be positive")

    if action.upper() == "BUY":
        if not (stop < entry < take):
            raise BracketOrderError(
                f"For BUY orders: stop ({stop:.2f}) < entry ({entry:.2f}) < take ({take:.2f}) required"
            )
    elif action.upper() == "SELL":
        if not (take < entry < stop):
            raise BracketOrderError(
                f"For SELL orders: take ({take:.2f}) < entry ({entry:.2f}) < stop ({stop:.2f}) required"
            )
    else:
        raise BracketOrderError(f"Invalid action: {action}. Must be BUY or SELL.")


def bracket_orders(
    action: str,
    quantity: int,
    limit_price: float,
    take_profit_price: float,
    stop_loss_price: float,
    validate: bool = True
) -> Tuple[Order, Order, Order]:
    """
    Create a bracket order (parent + take profit + stop loss).

    A bracket order consists of:
    - Parent order: Limit order to enter the position
    - Take profit: Limit order to exit at profit target (OCA with stop)
    - Stop loss: Stop order to exit at loss limit (OCA with take)

    The parent order has transmit=False so all three orders are submitted
    together atomically. Only the stop loss has transmit=True.

    Args:
        action: "BUY" or "SELL" for the entry direction
        quantity: Number of shares/contracts
        limit_price: Entry limit price
        take_profit_price: Take profit limit price
        stop_loss_price: Stop loss trigger price
        validate: If True, validate price relationships before creating orders

    Returns:
        Tuple of (parent_order, take_profit_order, stop_loss_order)

    Raises:
        BracketOrderError: If validate=True and prices are inconsistent
        ValueError: If quantity is not positive
    """
    if quantity <= 0:
        raise ValueError(f"Quantity must be positive, got {quantity}")

    if validate:
        validate_bracket_prices(action, limit_price, stop_loss_price, take_profit_price)

    parent = Order()
    parent.action = action.upper()
    parent.orderType = "LMT"
    parent.totalQuantity = float(quantity)
    parent.lmtPrice = float(limit_price)
    parent.tif = "DAY"
    parent.transmit = False
    parent.eTradeOnly = False
    parent.firmQuoteOnly = False

    take = Order()
    take.action = "SELL" if action.upper() == "BUY" else "BUY"
    take.orderType = "LMT"
    take.totalQuantity = float(quantity)
    take.lmtPrice = float(take_profit_price)
    take.tif = "GTC"
    take.transmit = False
    take.eTradeOnly = False
    take.firmQuoteOnly = False

    stop = Order()
    stop.action = "SELL" if action.upper() == "BUY" else "BUY"
    stop.orderType = "STP"
    stop.totalQuantity = float(quantity)
    stop.auxPrice = float(stop_loss_price)
    stop.tif = "GTC"
    stop.transmit = True
    stop.eTradeOnly = False
    stop.firmQuoteOnly = False

    return parent, take, stop
