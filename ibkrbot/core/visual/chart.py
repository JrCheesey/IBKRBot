from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

# Use matplotlib in a headless-safe way (cross-platform, works with PyInstaller)
import matplotlib
matplotlib.use("Agg")  # noqa: E402

from matplotlib.figure import Figure  # noqa: E402
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas  # noqa: E402


def save_price_thumbnail(
    times: Sequence[str],
    closes: Sequence[float],
    *,
    entry: float,
    stop: float,
    take: float,
    symbol: str,
    out_path: Path,
) -> Path:
    """
    Save a small PNG chart thumbnail to out_path.

    - Single plot only (no subplots)
    - No explicit colors specified (matplotlib defaults)
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig = Figure(figsize=(5.6, 2.0), dpi=120)
    _ = FigureCanvas(fig)
    ax = fig.add_subplot(111)

    # X axis: use integer positions to avoid datetime conversion + heavy formatting in thumbnails
    x = list(range(len(closes)))
    ax.plot(x, closes)

    # Entry/stop/take lines (defaults)
    if entry > 0:
        ax.axhline(entry, linestyle="--")
    if stop > 0:
        ax.axhline(stop, linestyle=":")
    if take > 0:
        ax.axhline(take, linestyle="--")

    ax.set_title(f"{symbol} (close)")
    ax.set_xlabel("Bars")
    ax.set_ylabel("Price")
    ax.grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(str(out_path), format="png")
    return out_path


def snapshot_from_dataframe(df, max_bars: int = 450) -> Dict[str, Any]:
    """
    Store a compact snapshot of time + Close series so we can regenerate the chart later.
    """
    if df is None or df.empty:
        return {"t": [], "close": []}
    d2 = df.tail(max_bars)
    times = [str(x) for x in d2.index.astype(str).tolist()]
    closes = [float(x) for x in d2["Close"].tolist()]
    return {"t": times, "close": closes}


def save_thumbnail_from_plan(plan: Dict[str, Any], *, out_path: Path) -> Path | None:
    """
    Regenerate a thumbnail from a plan snapshot, if present.
    """
    snap = plan.get("data_snapshot") or {}
    times = snap.get("t") or []
    closes = snap.get("close") or []
    if not times or not closes:
        return None
    lv = plan.get("levels", {})
    entry = float(lv.get("entry_limit", 0.0) or 0.0)
    stop = float(lv.get("stop", 0.0) or 0.0)
    take = float(lv.get("take_profit", 0.0) or 0.0)
    symbol = plan.get("symbol", "—")
    return save_price_thumbnail(times, closes, entry=entry, stop=stop, take=take, symbol=symbol, out_path=out_path)
