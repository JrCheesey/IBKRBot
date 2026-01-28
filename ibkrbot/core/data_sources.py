from __future__ import annotations
import logging
from dataclasses import dataclass
import threading
import pandas as pd

_log = logging.getLogger(__name__)

try:
    import yfinance as yf
except ImportError:  # pragma: no cover
    _log.warning("yfinance not installed - data fetching will not work")
    yf = None

from .task_runner import TaskContext


@dataclass
class PriceSeries:
    """Container for OHLCV price data."""
    df: pd.DataFrame  # Columns: Open, High, Low, Close, Volume


class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass


def _run_with_timeout(fn, timeout_s: float):
    """
    Run a blocking function in a daemon thread with a hard timeout.
    If the function does not finish in time, raise TimeoutError.
    """
    out = {"ok": False, "result": None, "err": None}
    def _wrap():
        try:
            out["result"] = fn()
            out["ok"] = True
        except Exception as e:
            out["err"] = e
    t = threading.Thread(target=_wrap, daemon=True)
    t.start()
    t.join(timeout=timeout_s)
    if t.is_alive():
        raise TimeoutError(f"Timed out after {timeout_s:.1f}s")
    if out["err"] is not None:
        raise out["err"]
    return out["result"]

def fetch_yahoo_ohlc(ctx: TaskContext, symbol: str, interval: str, lookback_days: int, timeout_s: float = 20.0) -> PriceSeries:
    """
    Fetch OHLCV data from Yahoo Finance with timeout protection.

    Args:
        ctx: TaskContext for progress reporting and cancellation
        symbol: Stock/ETF ticker symbol (e.g., 'SPY', 'AAPL')
        interval: Bar interval ('1h', '30m', '15m', '1d')
        lookback_days: Number of days of historical data to fetch
        timeout_s: Maximum seconds to wait for data (default: 20.0)

    Returns:
        PriceSeries containing DataFrame with Open, High, Low, Close, Volume

    Raises:
        RuntimeError: If yfinance not installed or data fetch fails
        TimeoutError: If data fetch exceeds timeout
        DataFetchError: If response data is invalid or missing required columns
    """
    if yf is None:
        raise RuntimeError("yfinance is not installed. Install requirements.txt")

    ctx.check_cancelled()
    period = f"{lookback_days}d"
    ctx.progress(f"Fetching Yahoo data: {symbol} ({period}, {interval})")
    t = yf.Ticker(symbol)

    ctx.check_cancelled()
    def _history():
        return t.history(period=period, interval=interval, auto_adjust=False, actions=False)

    df = _run_with_timeout(_history, timeout_s=timeout_s)
    ctx.check_cancelled()

    if df is None or df.empty:
        raise RuntimeError(f"No data from yfinance for {symbol} ({period}, {interval}).")

    df = df.rename(columns={c: c.title() for c in df.columns})
    needed = ["Open","High","Low","Close","Volume"]
    for c in needed:
        if c not in df.columns:
            raise RuntimeError(f"Missing column {c} in yfinance data for {symbol}.")
    ctx.progress(f"Downloaded {len(df)} bars for {symbol}.")
    return PriceSeries(df=df[needed].copy())

def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR) indicator.

    ATR measures market volatility by decomposing the entire range
    of an asset price for a given period. It is the average of
    true ranges over the specified period.

    True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)

    Args:
        df: DataFrame with 'High', 'Low', 'Close' columns
        period: Number of periods for moving average (default: 14)

    Returns:
        Series with ATR values (NaN for first period-1 values)
    """
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([(high-low).abs(), (high-prev_close).abs(), (low-prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()
