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
    direction: str = "Long",
) -> Path:
    """Save a PNG chart thumbnail with entry/stop/take levels."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig = Figure(figsize=(5.6, 2.0), dpi=120)
    _ = FigureCanvas(fig)
    ax = fig.add_subplot(111)

    x = list(range(len(closes)))
    ax.plot(x, closes, color="#333333", linewidth=1)

    # Color-coded lines: entry=blue, stop=red, take=green
    if entry > 0:
        ax.axhline(entry, linestyle="--", color="#2196F3", linewidth=1.5, label=f"Entry ${entry:.2f}")
    if stop > 0:
        ax.axhline(stop, linestyle=":", color="#F44336", linewidth=1.5, label=f"Stop ${stop:.2f}")
    if take > 0:
        ax.axhline(take, linestyle="--", color="#4CAF50", linewidth=1.5, label=f"Take ${take:.2f}")

    dir_label = "Short" if direction.lower() == "short" else "Long"
    ax.set_title(f"{symbol} ({dir_label})", fontsize=10)
    ax.set_xlabel("Bars", fontsize=8)
    ax.set_ylabel("Price", fontsize=8)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper left", fontsize=7)

    fig.tight_layout()
    fig.savefig(str(out_path), format="png")
    return out_path


def snapshot_from_dataframe(df, max_bars: int = 450) -> Dict[str, Any]:
    """Extract time + close series from dataframe for chart storage."""
    if df is None or df.empty:
        return {"t": [], "close": []}
    d2 = df.tail(max_bars)
    times = [str(x) for x in d2.index.astype(str).tolist()]
    closes = [float(x) for x in d2["Close"].tolist()]
    return {"t": times, "close": closes}


def save_thumbnail_from_plan(plan: Dict[str, Any], *, out_path: Path) -> Path | None:
    """Regenerate thumbnail from plan's data_snapshot."""
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
    direction = plan.get("direction", "Long")
    return save_price_thumbnail(times, closes, entry=entry, stop=stop, take=take, symbol=symbol, out_path=out_path, direction=direction)
