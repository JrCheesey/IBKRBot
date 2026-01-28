from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .paths import ensure_subdirs
from .constants import LoggingDefaults

def setup_logging() -> logging.Logger:
    dirs = ensure_subdirs()
    log_path: Path = dirs["logs"] / "ibkrbot.log"

    logger = logging.getLogger("ibkrbot")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if called twice
    if any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        return logger

    fmt = logging.Formatter(LoggingDefaults.FORMAT)

    # Use RotatingFileHandler to prevent unbounded log growth
    fh = RotatingFileHandler(
        log_path,
        encoding="utf-8",
        maxBytes=LoggingDefaults.MAX_BYTES,
        backupCount=LoggingDefaults.BACKUP_COUNT
    )
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    logger.propagate = False
    logger.info("Logging initialized. File: %s", str(log_path))
    return logger
