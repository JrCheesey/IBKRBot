from __future__ import annotations
import time
from typing import Dict
from ..task_runner import TaskContext
from ..ibkr.client import IbkrClient
from ..constants import Timeouts, OrderStatus, RetryDefaults

def cancel_open_brackets(ctx: TaskContext, ib: IbkrClient, symbol: str, retries: int = RetryDefaults.MAX_RETRIES, wait_s: float = RetryDefaults.DELAY_SEC) -> Dict[str, int]:
    """Cancel all active orders for symbol with retry/refresh."""
    attempted = 0
    cancel_requests = 0
    for i in range(retries):
        ctx.check_cancelled()
        ctx.progress(f"Cancel pass {i+1}/{retries}: refreshing open orders...")
        orders = ib.fetch_open_orders(timeout=Timeouts.IBKR_STANDARD)
        target = [o for o in orders if o.symbol == symbol and o.status not in OrderStatus.FINAL_STATES]
        if not target:
            return {"attempted": attempted, "cancelled": cancel_requests}

        ctx.progress(f"Found {len(target)} active orders for {symbol}. Sending cancel requests...")
        for o in target:
            ctx.check_cancelled()
            attempted += 1
            ib.cancel_order_safe(o.orderId)
            cancel_requests += 1

        time.sleep(wait_s)

    return {"attempted": attempted, "cancelled": cancel_requests}
