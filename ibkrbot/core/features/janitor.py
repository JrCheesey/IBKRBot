from __future__ import annotations
import datetime as dt
import logging
import re
from typing import Any, Dict, Tuple

from ..task_runner import TaskContext
from ..ibkr.client import IbkrClient
from ..constants import Timeouts, OrderStatus, AutomationDefaults
from .canceller import cancel_open_brackets

_log = logging.getLogger(__name__)


def parse_time_string(time_str: str) -> Tuple[int, int]:
    """Parse HH:MM to (hour, minute) tuple."""
    time_str = time_str.strip()
    pattern = r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$"
    match = re.match(pattern, time_str)
    if not match:
        raise ValueError(f"Invalid time format: '{time_str}'. Expected HH:MM (e.g., 15:45)")
    return int(match.group(1)), int(match.group(2))


def janitor_check_and_cancel(ctx: TaskContext, ib: IbkrClient, symbol: str, eod_local: str, stale_minutes: int) -> Dict[str, Any]:
    """Cancel orders if within EOD threshold."""
    now = dt.datetime.now()

    try:
        hh, mm = parse_time_string(eod_local)
    except ValueError as e:
        _log.error("Janitor: %s. Using default 15:45.", e)
        hh, mm = 15, 45

    eod = now.replace(hour=hh, minute=mm, second=0, microsecond=0)

    orders = ib.fetch_open_orders(timeout=Timeouts.IBKR_STANDARD)
    open_sym = [o for o in orders if o.symbol == symbol and o.status not in OrderStatus.FINAL_STATES]
    if not open_sym:
        return {"action":"none", "reason":"No open orders for symbol."}

    minutes_to_eod = (eod - now).total_seconds() / 60.0
    if minutes_to_eod <= AutomationDefaults.JANITOR_EOD_MINUTES:
        res = cancel_open_brackets(ctx, ib, symbol)
        return {"action":"cancel", "reason":f"Within {AutomationDefaults.JANITOR_EOD_MINUTES} min of EOD ({eod_local}).", **res}

    return {"action":"none", "reason":"Not near EOD; no auto-cancel.", "open_orders": len(open_sym)}
