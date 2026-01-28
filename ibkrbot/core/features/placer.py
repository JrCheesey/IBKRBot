from __future__ import annotations
from typing import Any, Dict, Optional
import json
import time

from ..task_runner import TaskContext
from ..ibkr.client import IbkrClient
from ..ibkr.contracts import from_symbol_cfg
from ..ibkr.orders import bracket_orders
from ..plan import now_iso, latest_plan, load_json
from ..constants import Timeouts, OrderStatus
from ..ibkr.error_codes import IBKRErrorCodes

class DuplicateBracketError(RuntimeError):
    pass

def _has_active_orders(open_orders, symbol: str) -> bool:
    return any(o.symbol == symbol and o.status not in OrderStatus.FINAL_STATES for o in open_orders)

def _has_open_position(positions, symbol: str) -> bool:
    for p in positions:
        if p.get("symbol") == symbol and abs(float(p.get("position", 0.0))) > 0.0:
            return True
    return False

def _recent_placed_plan(symbol: str) -> Optional[Dict[str, Any]]:
    p = latest_plan(symbol, "placed")
    if p and p.exists():
        try:
            return load_json(p)
        except Exception:
            return None
    return None

def _friendly_reject(err: tuple[int,int,str,str]) -> str:
    reqId, code, msg, adv = err

    # Try to get friendly error message from error codes module
    error_info = IBKRErrorCodes.get_friendly_message(code, msg)
    base = f"IBKR {error_info['title']} (code {code}): {error_info['message']}"

    if error_info['hint']:
        base += f"\n\nHint: {error_info['hint']}"

    # Additional context for known error codes
    if code in (IBKRErrorCodes.PERMISSION_DENIED, IBKRErrorCodes.INVALID_ORDER, IBKRErrorCodes.ROUTING_ERROR):
        base += (
            "\n\nTroubleshooting:"
            "\n- Confirm IB Gateway is in PAPER and API is enabled (socket clients)."
            "\n- Confirm clientId is not used by another app."
            "\n- Refresh open orders, then retry."
        )

    # Canada / TSE hints
    if any(k in msg.lower() for k in ["canada", "canadian", "tse", "toronto", "cad"]):
        base += (
            "\n\nCanadian ETF note:"
            "\nSome IBKR account settings/permissions can disallow API orders for certain Canadian listings."
            "\nTry SPY (US) to validate API connectivity, then review trading permissions for CAD products."
        )

    if adv:
        # Keep it short: advanced JSON can be large; show first ~300 chars.
        base += f"\n\nAdvanced reject details (truncated): {adv[:300]}"

    return base

def place_bracket_from_plan(ctx: TaskContext, ib: IbkrClient, symbol_cfg: Dict[str, Any], plan: Dict[str, Any], no_dupe_block_on_position: bool = True) -> Dict[str, Any]:
    symbol = plan["symbol"]

    # Extra guard: if we placed recently, don't allow a second bracket unless user cancels first.
    recent = _recent_placed_plan(symbol)
    if recent and recent.get("status", {}).get("placed"):
        parent_id = recent.get("status", {}).get("ibkr", {}).get("parent_order_id")
        if parent_id:
            # If open orders show anything active for symbol, block.
            try:
                orders = ib.fetch_open_orders(timeout=Timeouts.IBKR_STANDARD)
                if _has_active_orders(orders, symbol):
                    raise DuplicateBracketError(f"Active orders already exist for {symbol}. Cancel first (No duplicates rule).")
            except Exception:
                # If we can't verify, still block to be safe.
                raise DuplicateBracketError(f"Recent placed plan detected for {symbol}. Refresh/cancel existing orders before placing again.")

    # Refresh open orders and positions
    ctx.progress("Checking for existing orders/positions (no-duplicates rule)...")
    orders = ib.fetch_open_orders(timeout=Timeouts.IBKR_STANDARD)
    if _has_active_orders(orders, symbol):
        raise DuplicateBracketError(f"Active orders already exist for {symbol}. Cancel first (No duplicates rule).")

    if no_dupe_block_on_position:
        positions = ib.fetch_positions(timeout=Timeouts.IBKR_STANDARD)
        if _has_open_position(positions, symbol):
            raise DuplicateBracketError(f"Position already exists for {symbol}. Close/flatten before placing a new bracket (No duplicates rule).")

    qty = int(plan["risk"]["qty"])
    entry = float(plan["levels"]["entry_limit"])
    stop = float(plan["levels"]["stop"])
    take = float(plan["levels"]["take_profit"])
    action = plan.get("action", "BUY")  # Default to BUY for backwards compatibility

    contract = from_symbol_cfg(symbol_cfg)
    parent, take_o, stop_o = bracket_orders(action, qty, entry, take, stop)

    parent_id = ib.next_order_id()
    take_id = ib.next_order_id()
    stop_id = ib.next_order_id()

    parent.orderId = parent_id
    take_o.orderId = take_id
    stop_o.orderId = stop_id

    take_o.parentId = parent_id
    stop_o.parentId = parent_id

    ib.clear_last_error()

    # Submit
    ctx.progress("Submitting bracket orders to IBKR...")
    ib.placeOrder(parent_id, contract, parent)
    ctx.check_cancelled()
    ib.placeOrder(take_id, contract, take_o)
    ctx.check_cancelled()
    ib.placeOrder(stop_id, contract, stop_o)

    # Best-effort confirm: wait briefly for orderStatus, and check for immediate rejection
    st = ib.wait_for_order_status(stop_id, timeout=Timeouts.IBKR_ORDER_STATUS)
    if st is None:
        err = ib.last_error()
        if err:
            raise RuntimeError(_friendly_reject(err))
    elif st.lower() in ("rejected", "inactive"):
        err = ib.last_error()
        if err:
            raise RuntimeError(_friendly_reject(err))
        raise RuntimeError(f"Order status indicates failure: {st}")

    plan2 = json.loads(json.dumps(plan))  # deep copy
    plan2["status"]["placed"] = True
    plan2["status"]["ibkr"].update({
        "parent_order_id": parent_id,
        "take_order_id": take_id,
        "stop_order_id": stop_id,
        "last_submit_at": now_iso(),
        "last_error": None,
    })
    return plan2
