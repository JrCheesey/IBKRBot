from __future__ import annotations
import logging
from PySide6.QtCore import QObject, Signal

class QtLogEmitter(QObject):
    message = Signal(str)

class QtLogHandler(logging.Handler):
    def __init__(self, emitter: QtLogEmitter):
        super().__init__()
        self.emitter = emitter

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.emitter.message.emit(msg)
        except Exception:
            pass
