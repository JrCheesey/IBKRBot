from __future__ import annotations
import traceback
from dataclasses import dataclass
from typing import Any, Callable, Optional
import threading

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

class TaskSignals(QObject):
    started = Signal(str)
    progress = Signal(str)
    log = Signal(str)
    finished = Signal(object)
    error = Signal(str)
    cancelled = Signal()

@dataclass
class TaskContext:
    cancel_event: threading.Event
    progress: Callable[[str], None]
    log: Callable[[str], None]

    def check_cancelled(self) -> None:
        if self.cancel_event.is_set():
            raise TaskCancelled()

class TaskCancelled(Exception):
    pass

class Task(QRunnable):
    """
    Run a callable in a worker thread. Supports cooperative cancellation and progress/log callbacks.
    """
    def __init__(self, name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any):
        super().__init__()
        self.name = name
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = TaskSignals()
        self.cancel_event = threading.Event()
        self.setAutoDelete(True)

    def cancel(self) -> None:
        self.cancel_event.set()

    @Slot()
    def run(self) -> None:
        self.signals.started.emit(self.name)
        try:
            ctx = TaskContext(
                cancel_event=self.cancel_event,
                progress=lambda m: self.signals.progress.emit(m),
                log=lambda m: self.signals.log.emit(m),
            )
            result = self.fn(ctx, *self.args, **self.kwargs)
            if self.cancel_event.is_set():
                self.signals.cancelled.emit()
                return
            self.signals.finished.emit(result)
        except TaskCancelled:
            self.signals.cancelled.emit()
        except Exception:
            self.signals.error.emit(traceback.format_exc())

class TaskRunner(QObject):
    """
    Owns a threadpool and tracks a single 'busy' foreground task.
    Prevents double-click crashes by allowing only one task at a time.
    """
    busy_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.pool = QThreadPool.globalInstance()
        self._busy = False
        self._current: Optional[Task] = None

    @property
    def busy(self) -> bool:
        return self._busy

    def start(self, task: Task) -> None:
        if self._busy:
            task.signals.error.emit("Busy: a task is already running. Please wait or cancel it.")
            return

        self._busy = True
        self._current = task
        self.busy_changed.emit(True)

        def _done(*_args: Any) -> None:
            self._busy = False
            self._current = None
            self.busy_changed.emit(False)

        task.signals.finished.connect(_done)
        task.signals.error.connect(_done)
        task.signals.cancelled.connect(_done)

        self.pool.start(task)

    def cancel_current(self) -> None:
        if self._current is not None:
            self._current.cancel()
