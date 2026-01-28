from __future__ import annotations
from typing import Any, Dict
from ..task_runner import TaskContext
from ..ibkr.client import IbkrClient
from ..constants import Timeouts

def fetch_orders_and_positions(ctx: TaskContext, ib: IbkrClient) -> Dict[str, Any]:
    ctx.check_cancelled()
    orders = ib.fetch_open_orders(timeout=Timeouts.IBKR_STANDARD)
    ctx.check_cancelled()
    positions = ib.fetch_positions(timeout=Timeouts.IBKR_STANDARD)
    return {"orders": orders, "positions": positions}
