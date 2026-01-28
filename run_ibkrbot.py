"""Entry-point wrapper for both dev runs and PyInstaller builds."""
from __future__ import annotations

import sys
from pathlib import Path

def _bootstrap_path() -> None:
    # In a PyInstaller build, resources may live under sys._MEIPASS.
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(getattr(sys, "_MEIPASS"))  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parent

    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

_bootstrap_path()

from ibkrbot.main import main

if __name__ == "__main__":
    main()
