from __future__ import annotations
import os
import sys
from pathlib import Path

APP_NAME = "IBKRBot"

def is_frozen() -> bool:
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

def resource_path(relative: str) -> Path:
    """
    Return an absolute Path to a bundled resource, working both from source and PyInstaller builds.

    We bundle resources into: ibkrbot/resources/ (both source tree and PyInstaller datas).
    """
    if is_frozen():
        base = Path(sys._MEIPASS) / "ibkrbot" / "resources"  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parents[1] / "resources"
    return (base / relative).resolve()

def user_data_dir() -> Path:
    """
    Where we write mutable data (plans, logs, user config). Never write to the install folder.

    Cross-platform data directory:
    - Windows: %APPDATA%/IBKRBot
    - macOS: ~/Library/Application Support/IBKRBot
    - Linux: ~/.config/IBKRBot
    """
    if sys.platform == "win32":
        # Windows: use APPDATA
        appdata = os.environ.get("APPDATA")
        root = Path(appdata) / APP_NAME if appdata else (Path.home() / APP_NAME)
    elif sys.platform == "darwin":
        # macOS: use ~/Library/Application Support
        root = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        # Linux and others: use XDG_CONFIG_HOME or ~/.config
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        root = Path(xdg_config) / APP_NAME if xdg_config else (Path.home() / ".config" / APP_NAME)

    d = root.resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d

def ensure_subdirs() -> dict[str, Path]:
    root = user_data_dir()
    plans = root / "plans"
    logs = root / "logs"
    thumbs = root / "thumbs"
    plans.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    thumbs.mkdir(parents=True, exist_ok=True)
    return {"root": root, "plans": plans, "logs": logs, "thumbs": thumbs}
