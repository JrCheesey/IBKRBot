"""Sound notifications - cross-platform."""
import sys
import logging

_log = logging.getLogger(__name__)

# Sound types
SOUND_SUCCESS = "success"
SOUND_ERROR = "error"
SOUND_WARNING = "warning"
SOUND_ORDER_FILLED = "order_filled"
SOUND_ORDER_PLACED = "order_placed"
SOUND_ALERT = "alert"
SOUND_CONNECT = "connect"
SOUND_DISCONNECT = "disconnect"

# Windows beep frequencies (Hz, ms)
_WIN_BEEPS = {
    SOUND_SUCCESS: (1000, 200),
    SOUND_ERROR: (400, 500),
    SOUND_WARNING: (600, 300),
    SOUND_ORDER_FILLED: (1200, 300),
    SOUND_ORDER_PLACED: (800, 200),
    SOUND_ALERT: (1000, 400),
    SOUND_CONNECT: (1500, 200),
    SOUND_DISCONNECT: (300, 400),
}


class SoundPlayer:
    """Plays notification sounds."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._enabled = True
            cls._instance._init_done = False
        return cls._instance

    def __init__(self):
        if self._init_done:
            return
        self._init_done = True

        # Check for Qt
        self._use_qt = False
        try:
            from PySide6.QtWidgets import QApplication
            self._use_qt = True
        except ImportError:
            pass

    @property
    def enabled(self):
        return self._enabled

    @enabled.setter
    def enabled(self, val):
        self._enabled = bool(val)

    def play(self, sound_type=SOUND_ALERT):
        if not self._enabled:
            return

        try:
            # Try Qt beep first
            if self._use_qt:
                from PySide6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    app.beep()
                    return

            # Fallback to system beep
            if sys.platform == "win32":
                import winsound
                freq, ms = _WIN_BEEPS.get(sound_type, (1000, 200))
                winsound.Beep(freq, ms)
            else:
                print('\a', end='', flush=True)
        except Exception:
            pass


_player = None

def get_sound_player():
    global _player
    if _player is None:
        _player = SoundPlayer()
    return _player
