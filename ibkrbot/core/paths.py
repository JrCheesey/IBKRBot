"""Path utilities for IBKRBot."""
import os
import sys
from pathlib import Path

APP_NAME = "IBKRBot"


def is_frozen():
    """Check if running as PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def resource_path(relative):
    """Get path to bundled resource file."""
    if is_frozen():
        base = Path(sys._MEIPASS) / "ibkrbot" / "resources"
    else:
        base = Path(__file__).resolve().parents[1] / "resources"
    return (base / relative).resolve()


def user_data_dir():
    """
    Get user data directory (plans, logs, config).
    - Windows: %APPDATA%/IBKRBot
    - macOS: ~/Library/Application Support/IBKRBot
    - Linux: ~/.config/IBKRBot (or $XDG_CONFIG_HOME)
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        root = Path(appdata) / APP_NAME if appdata else Path.home() / APP_NAME
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / APP_NAME
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        root = Path(xdg) / APP_NAME if xdg else Path.home() / ".config" / APP_NAME

    root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_subdirs():
    """Create and return paths dict for plans, logs, thumbs."""
    root = user_data_dir()
    paths = {
        "root": root,
        "plans": root / "plans",
        "logs": root / "logs",
        "thumbs": root / "thumbs",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths
