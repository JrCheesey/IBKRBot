from __future__ import annotations
import threading
import time
from typing import Any, Dict, Optional

from PySide6.QtCore import QObject, Signal

from ..plan import latest_plan, load_json
from ..ibkr.contracts import from_symbol_cfg
from ..constants import Timeouts, OrderStatus, RiskDefaults, AutomationDefaults

class ManagerWorker(QObject):
    log = Signal(str)
    stopped = Signal()

    def __init__(self, ib, cfg: Dict[str, Any], symbol_cfg: Dict[str, Any]):
        super().__init__()
        self.ib = ib
        self.cfg = cfg
        self.symbol_cfg = symbol_cfg
        self._stop_event = threading.Event()
        # Check if snapshot price is enabled (default: False to avoid subscription errors)
        self._snapshot_enabled = cfg.get("manager", {}).get("enable_snapshot_price", False)

    def stop(self) -> None:
        self._stop_event.set()

    def _load_placed_plan(self, symbol: str) -> Optional[Dict[str, Any]]:
        p = latest_plan(symbol, "placed")
        if p and p.exists():
            try:
                return load_json(p)
            except Exception:
                return None
        return None

    def run(self) -> None:
        poll = float(self.cfg["manager"]["poll_seconds"])
        symbol = self.symbol_cfg["symbol"]
        contract = from_symbol_cfg(self.symbol_cfg)

        self.log.emit(f"Manager started for {symbol} (poll={poll}s)")
        try:
            while not self._stop_event.is_set():
                # Use short timeouts so stop responds quickly
                try:
                    orders = self.ib.fetch_open_orders(timeout=Timeouts.IBKR_QUICK)
                except Exception as e:
                    orders = []
                    self.log.emit(f"orders fetch error: {e}")

                if self._stop_event.is_set():
                    break

                try:
                    positions = self.ib.fetch_positions(timeout=Timeouts.IBKR_QUICK)
                except Exception as e:
                    positions = []
                    self.log.emit(f"positions fetch error: {e}")

                o_sym = [o for o in orders if o.symbol == symbol and o.status not in OrderStatus.FINAL_STATES]
                p_sym = [p for p in positions if p.get("symbol") == symbol and abs(p.get("position",0)) > 0]
                self.log.emit(f"[{symbol}] open_orders={len(o_sym)} positions={len(p_sym)}")

                # R-multiple (best-effort): needs placed plan + snapshot price
                plan = self._load_placed_plan(symbol)
                if plan and p_sym and self._snapshot_enabled:
                    entry = float(plan["levels"].get("entry_limit") or plan["levels"].get("last_close") or 0.0)
                    stop = float(plan["levels"].get("stop") or 0.0)
                    direction = plan.get("direction", "Long")
                    # For short positions, risk calculation is different
                    if direction == "Short":
                        rps = max(stop - entry, RiskDefaults.EPSILON)
                    else:
                        rps = max(entry - stop, RiskDefaults.EPSILON)
                    px = None
                    try:
                        px = self.ib.snapshot_price(contract, timeout=Timeouts.IBKR_QUICK)
                    except Exception:
                        px = None
                    if px:
                        if direction == "Short":
                            r = (entry - float(px)) / rps
                        else:
                            r = (float(px) - entry) / rps
                        self.log.emit(f"[{symbol}] ({direction}) price={px:.2f} entry={entry:.2f} stop={stop:.2f} R={r:.2f}")
                    else:
                        self.log.emit(f"[{symbol}] price snapshot unavailable (permissions/delay).")
                elif plan and p_sym and not self._snapshot_enabled:
                    self.log.emit(f"[{symbol}] snapshot price disabled in settings.")

                # Sleep in small increments so stop triggers quickly
                slept = 0.0
                while slept < poll and not self._stop_event.is_set():
                    time.sleep(0.2)
                    slept += 0.2
        finally:
            self.log.emit("Manager stopped.")
            self.stopped.emit()
