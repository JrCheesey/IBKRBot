from __future__ import annotations
from typing import Tuple
from ibapi.order import Order


class BracketOrderError(Exception):
    pass


def validate_bracket_prices(action: str, entry: float, stop: float, take: float) -> None:
    """Validate bracket price relationships for BUY/SELL."""
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
    """Create bracket order: parent LMT + take LMT + stop STP."""
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
