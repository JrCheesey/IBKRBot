from __future__ import annotations
import threading
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.order import Order
from ibapi.contract import Contract
from ibapi.order_state import OrderState

@dataclass
class OpenOrderRow:
    orderId: int
    symbol: str
    action: str
    orderType: str
    totalQuantity: float
    lmtPrice: float
    auxPrice: float
    status: str
    parentId: int

# last_error: (reqId, errorCode, errorString, advancedRejectJson)
LastError = Tuple[int, int, str, str]

class IbkrClient(EWrapper, EClient):
    def __init__(self, logger):
        EClient.__init__(self, wrapper=self)
        self._logger = logger
        self._thread: Optional[threading.Thread] = None

        self._next_id_lock = threading.Lock()
        self._next_valid_id: Optional[int] = None
        self._next_id_evt = threading.Event()

        self._acct_lock = threading.Lock()
        self._netliq: Optional[float] = None
        self._acct_evt = threading.Event()
        self._acct_req_id = 9001

        self._open_orders_lock = threading.Lock()
        self._open_orders: List[OpenOrderRow] = []
        self._open_orders_evt = threading.Event()

        self._positions_lock = threading.Lock()
        self._positions: List[Dict[str, Any]] = []
        self._positions_evt = threading.Event()

        self._errors_lock = threading.Lock()
        self._last_error: Optional[LastError] = None

        self._order_status_lock = threading.Lock()
        self._order_status: Dict[int, str] = {}
        self._order_status_evts: Dict[int, threading.Event] = {}

        self._mkt_lock = threading.Lock()
        self._mkt_prices: Dict[int, float] = {}
        self._mkt_evts: Dict[int, threading.Event] = {}

        self._req_id_lock = threading.Lock()
        self._next_req_id = 10001

    # --- callbacks ---
    def nextValidId(self, orderId: int):
        with self._next_id_lock:
            self._next_valid_id = int(orderId)
        self._next_id_evt.set()
        self._logger.info("IBKR nextValidId: %s", orderId)

    def error(self, reqId: int, errorCode: int, errorString: str, advancedOrderRejectJson: str = ""):
        with self._errors_lock:
            self._last_error = (int(reqId), int(errorCode), str(errorString), str(advancedOrderRejectJson or ""))
        self._logger.warning("IBKR error reqId=%s code=%s %s", reqId, errorCode, errorString)

        # Wake any waiter on this orderId
        try:
            oid = int(reqId)
        except Exception:
            oid = None
        if oid is not None:
            with self._order_status_lock:
                evt = self._order_status_evts.get(oid)
            if evt:
                evt.set()

    def orderStatus(self, orderId: int, status: str, filled: float, remaining: float, avgFillPrice: float,
                    permId: int, parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        with self._order_status_lock:
            self._order_status[int(orderId)] = str(status)
            evt = self._order_status_evts.get(int(orderId))
        if evt:
            evt.set()

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        if reqId == self._acct_req_id and tag == "NetLiquidation":
            try:
                v = float(value)
            except Exception:
                v = None
            with self._acct_lock:
                self._netliq = v
            self._logger.info("NetLiquidation: %s %s", value, currency)

    def accountSummaryEnd(self, reqId: int):
        if reqId == self._acct_req_id:
            self._acct_evt.set()

    def openOrder(self, orderId: int, contract: Contract, order: Order, orderState: OrderState):
        sym = getattr(contract, "symbol", "")
        row = OpenOrderRow(
            orderId=int(orderId),
            symbol=str(sym),
            action=str(order.action),
            orderType=str(order.orderType),
            totalQuantity=float(order.totalQuantity),
            lmtPrice=float(getattr(order, "lmtPrice", 0.0) or 0.0),
            auxPrice=float(getattr(order, "auxPrice", 0.0) or 0.0),
            status=str(orderState.status),
            parentId=int(getattr(order, "parentId", 0) or 0),
        )
        with self._open_orders_lock:
            self._open_orders.append(row)

    def openOrderEnd(self):
        self._open_orders_evt.set()

    def position(self, account: str, contract: Contract, position: float, avgCost: float):
        sym = getattr(contract, "symbol", "")
        with self._positions_lock:
            self._positions.append({
                "account": account,
                "symbol": sym,
                "position": float(position),
                "avgCost": float(avgCost),
                "currency": getattr(contract, "currency", ""),
            })

    def positionEnd(self):
        self._positions_evt.set()

    # Market data (snapshot)
    def tickPrice(self, reqId: int, tickType: int, price: float, attrib):
        if price is None:
            return
        try:
            p = float(price)
        except Exception:
            return
        if p <= 0:
            return
        with self._mkt_lock:
            if reqId not in self._mkt_prices:
                self._mkt_prices[reqId] = p
            evt = self._mkt_evts.get(reqId)
        if evt:
            evt.set()

    def tickSnapshotEnd(self, reqId: int):
        with self._mkt_lock:
            evt = self._mkt_evts.get(reqId)
        if evt:
            evt.set()

    # --- lifecycle ---
    def connect_and_start(self, host: str, port: int, client_id: int, timeout: float = 6.0) -> None:
        if self.isConnected():
            return
        self._logger.info("Connecting to IBKR %s:%s clientId=%s", host, port, client_id)
        self._next_id_evt.clear()
        super().connect(host, int(port), int(client_id))
        self._thread = threading.Thread(target=self.run, name="IBKRApiThread", daemon=True)
        self._thread.start()
        if not self._next_id_evt.wait(timeout=timeout):
            raise TimeoutError("Timed out waiting for IBKR nextValidId (API not ready).")

    def disconnect_and_stop(self, timeout: float = 2.0) -> None:
        if not self.isConnected():
            return
        self._logger.info("Disconnecting IBKR...")
        try:
            self.disconnect()
        except Exception:
            pass
        if self._thread:
            self._thread.join(timeout=timeout)

    # --- request ids ---
    def next_req_id(self) -> int:
        with self._req_id_lock:
            rid = self._next_req_id
            self._next_req_id += 1
            return rid

    # --- helpers ---
    def next_order_id(self) -> int:
        with self._next_id_lock:
            if self._next_valid_id is None:
                raise RuntimeError("Not connected (no nextValidId).")
            oid = self._next_valid_id
            self._next_valid_id += 1
            return oid

    def last_error(self) -> Optional[LastError]:
        with self._errors_lock:
            return self._last_error

    def clear_last_error(self) -> None:
        with self._errors_lock:
            self._last_error = None

    def get_order_status(self, order_id: int) -> Optional[str]:
        with self._order_status_lock:
            return self._order_status.get(int(order_id))

    def wait_for_order_status(self, order_id: int, timeout: float = 4.0) -> Optional[str]:
        oid = int(order_id)
        evt = threading.Event()
        with self._order_status_lock:
            self._order_status_evts[oid] = evt
        try:
            evt.wait(timeout=timeout)
            return self.get_order_status(oid)
        finally:
            with self._order_status_lock:
                self._order_status_evts.pop(oid, None)

    def get_net_liq(self, timeout: float = 6.0) -> float:
        self._acct_evt.clear()
        with self._acct_lock:
            self._netliq = None
        self.reqAccountSummary(self._acct_req_id, "All", "NetLiquidation")
        if not self._acct_evt.wait(timeout=timeout):
            raise TimeoutError("Timed out waiting for account summary.")
        with self._acct_lock:
            if self._netliq is None:
                raise RuntimeError("NetLiquidation unavailable.")
            return float(self._netliq)

    def fetch_open_orders(self, timeout: float = 6.0) -> List[OpenOrderRow]:
        self._open_orders_evt.clear()
        with self._open_orders_lock:
            self._open_orders = []
        self.reqOpenOrders()
        if not self._open_orders_evt.wait(timeout=timeout):
            raise TimeoutError("Timed out waiting for open orders.")
        with self._open_orders_lock:
            return list(self._open_orders)

    def fetch_positions(self, timeout: float = 6.0) -> List[Dict[str, Any]]:
        self._positions_evt.clear()
        with self._positions_lock:
            self._positions = []
        self.reqPositions()
        if not self._positions_evt.wait(timeout=timeout):
            raise TimeoutError("Timed out waiting for positions.")
        with self._positions_lock:
            return list(self._positions)

    def cancel_order_safe(self, order_id: int) -> None:
        try:
            self.cancelOrder(int(order_id))
        except Exception as e:
            self._logger.warning("cancelOrder failed for %s: %s", order_id, e)

    def snapshot_price(self, contract: Contract, timeout: float = 3.0) -> Optional[float]:
        """
        Best-effort snapshot price via IB market data. May be delayed/unavailable depending on permissions.
        """
        req_id = self.next_req_id()
        evt = threading.Event()
        with self._mkt_lock:
            self._mkt_prices.pop(req_id, None)
            self._mkt_evts[req_id] = evt
        try:
            self.reqMktData(req_id, contract, "", True, False, [])
            evt.wait(timeout=timeout)
            with self._mkt_lock:
                return self._mkt_prices.get(req_id)
        finally:
            try:
                self.cancelMktData(req_id)
            except Exception:
                pass
            with self._mkt_lock:
                self._mkt_evts.pop(req_id, None)
                self._mkt_prices.pop(req_id, None)
