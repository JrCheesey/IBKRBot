from __future__ import annotations
from typing import Any, Dict, Optional
from ibapi.contract import Contract

def stock_contract(symbol: str, currency: str = "USD", exchange: str = "SMART", primaryExchange: Optional[str] = None) -> Contract:
    c = Contract()
    c.symbol = symbol
    c.secType = "STK"
    c.currency = currency
    c.exchange = exchange
    if primaryExchange:
        c.primaryExchange = primaryExchange
    return c

def from_symbol_cfg(symbol_cfg: Dict[str, Any]) -> Contract:
    return stock_contract(
        symbol=symbol_cfg["symbol"],
        currency=symbol_cfg.get("currency", "USD"),
        exchange="SMART",
        primaryExchange=symbol_cfg.get("primaryExchange") or symbol_cfg.get("exchange"),
    )
