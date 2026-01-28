from __future__ import annotations

import logging
from typing import Any, Dict

from ..task_runner import TaskContext
from ..data_sources import fetch_yahoo_ohlc, atr
from ..plan import now_iso
from ..paths import ensure_subdirs
from ..visual.chart import snapshot_from_dataframe, save_price_thumbnail

_log = logging.getLogger(__name__)


class ProposalError(Exception):
    """Raised when plan proposal fails due to invalid data or calculation errors."""
    pass


def propose_swing_plan(ctx: TaskContext, symbol_cfg: Dict[str, Any], cfg: Dict[str, Any], net_liq: float) -> Dict[str, Any]:
    """
    Generate a swing trading plan proposal based on ATR pullback strategy.

    This function:
    1. Fetches historical OHLC data from Yahoo Finance
    2. Computes ATR for volatility-based levels
    3. Calculates entry, stop, and take profit prices
    4. Determines position size based on risk limits
    5. Generates a chart thumbnail for visual review

    Args:
        ctx: TaskContext for progress reporting and cancellation
        symbol_cfg: Symbol configuration dict with 'symbol', 'exchange', 'currency'
        cfg: Full application configuration dict
        net_liq: Account net liquidation value

    Returns:
        Complete plan dict ready for saving and placement

    Raises:
        ProposalError: If calculation fails (insufficient data, invalid prices, etc.)
        RuntimeError: If ATR cannot be computed or quantity is zero
    """
    symbol = symbol_cfg["symbol"]
    interval = cfg["strategy"]["bar_interval"]
    lookback = int(cfg["strategy"]["lookback_days"])
    atr_period = int(cfg["strategy"]["atr_period"])
    pullback_pct = float(cfg["strategy"]["pullback_pct"])
    stop_atr_mult = float(cfg["strategy"]["stop_atr_mult"])
    limit_offset_atr = float(cfg["strategy"]["limit_offset_atr"])
    take_r = float(cfg["risk"]["r_multiple_take"])
    yf_timeout = float(cfg.get("data", {}).get("yfinance_timeout_s", 20.0))

    ctx.progress(f"Proposing swing plan for {symbol}...")
    ps = fetch_yahoo_ohlc(ctx, symbol, interval, lookback, timeout_s=yf_timeout)
    df = ps.df

    ctx.progress("Computing ATR...")
    a = atr(df, atr_period)
    if a.dropna().empty:
        raise RuntimeError("ATR could not be computed (not enough bars).")
    atr_v = float(a.dropna().iloc[-1])
    last_close = float(df["Close"].iloc[-1])

    entry = round(last_close - (pullback_pct * atr_v) - (limit_offset_atr * atr_v), 2)
    stop = round(entry - (stop_atr_mult * atr_v), 2)
    risk_per_share = max(entry - stop, 0.01)
    take = round(entry + take_r * risk_per_share, 2)

    max_notional = float(cfg["risk"]["max_notional_pct"]) * net_liq
    max_loss = float(cfg["risk"]["max_loss_pct"]) * net_liq

    qty_by_loss = int(max_loss / risk_per_share)
    qty_by_notional = int(max_notional / max(entry, 0.01))
    qty = max(0, min(qty_by_loss, qty_by_notional))

    if qty <= 0:
        # Provide detailed error message explaining why qty is 0
        error_details = (
            f"Calculated quantity is 0. Cannot build plan.\n\n"
            f"Details:\n"
            f"  Entry price: ${entry:.2f}\n"
            f"  Risk per share: ${risk_per_share:.2f}\n"
            f"  Max notional: ${max_notional:.2f} ({cfg['risk']['max_notional_pct']*100:.1f}% of NetLiq)\n"
            f"  Max loss: ${max_loss:.2f} ({cfg['risk']['max_loss_pct']*100:.2f}% of NetLiq)\n"
            f"  Qty by notional limit: {qty_by_notional} shares\n"
            f"  Qty by loss limit: {qty_by_loss} shares\n\n"
        )

        if qty_by_notional <= 0:
            error_details += "❌ Notional limit is too low for this symbol's price.\n"
            error_details += "   → Increase max_notional_pct in Settings (Risk tab)\n"
            error_details += "   → Or choose a lower-priced symbol\n"
        elif qty_by_loss <= 0:
            error_details += "❌ Loss limit is too low for the risk per share.\n"
            error_details += "   → Increase max_loss_pct in Settings (Risk tab)\n"
            error_details += "   → Or choose a less volatile symbol (lower ATR)\n"

        raise ProposalError(error_details)

    ctx.progress("Draft plan built.")

    # Validate price relationships for long bracket
    if not (stop < entry < take):
        raise ProposalError(
            f"Invalid price levels: stop ({stop:.2f}) < entry ({entry:.2f}) < take ({take:.2f}) required for long bracket"
        )

    # Compact snapshot + thumbnail for UI preview.
    snap = snapshot_from_dataframe(df, max_bars=int(cfg.get("ui", {}).get("thumbnail_max_bars", 450)))
    thumb_rel = None
    try:
        paths = ensure_subdirs()
        fname = f"{symbol}_draft.png"
        thumb_path = paths["thumbs"] / fname
        save_price_thumbnail(
            snap.get("t", []),
            snap.get("close", []),
            entry=entry,
            stop=stop,
            take=take,
            symbol=symbol,
            out_path=thumb_path,
        )
        thumb_rel = f"thumbs/{fname}"
    except Exception as e:
        _log.warning("Failed to generate chart thumbnail for %s: %s", symbol, e)
        thumb_rel = None

    return {
        "version": "2",
        "created_at": now_iso(),
        "symbol": symbol,
        "listing": {
            "exchange": symbol_cfg.get("exchange", "SMART"),
            "currency": symbol_cfg.get("currency", "USD"),
            "primaryExchange": symbol_cfg.get("primaryExchange"),
        },
        "mode": cfg["ibkr"]["mode"],
        "source": {"provider": "yfinance", "interval": interval, "lookback_days": lookback},
        "data_snapshot": snap,
        "artifacts": {"thumbnail_rel": thumb_rel},
        "strategy": {
            "name": "swing_pullback_atr",
            "atr_period": atr_period,
            "pullback_pct": pullback_pct,
            "stop_atr_mult": stop_atr_mult,
            "limit_offset_atr": limit_offset_atr,
        },
        "risk": {
            "net_liq": net_liq,
            "max_notional_pct": float(cfg["risk"]["max_notional_pct"]),
            "max_loss_pct": float(cfg["risk"]["max_loss_pct"]),
            "max_notional": max_notional,
            "max_loss": max_loss,
            "qty": qty,
            "estimated_notional": qty * entry,
            "estimated_risk": qty * risk_per_share,
            "take_r": take_r,
        },
        "levels": {
            "last_close": last_close,
            "atr": atr_v,
            "entry_limit": entry,
            "stop": stop,
            "take_profit": take,
            "risk_per_share": risk_per_share,
        },
        "status": {
            "draft": True,
            "placed": False,
            "ibkr": {
                "parent_order_id": None,
                "take_order_id": None,
                "stop_order_id": None,
                "last_submit_at": None,
                "last_error": None,
            },
        },
        "notes": [
            "Human-in-the-loop: review before placing.",
            "Paper accounts may show simulated NetLiq (often 1,000,000).",
        ],
    }
