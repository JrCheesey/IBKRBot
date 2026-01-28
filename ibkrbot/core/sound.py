"""
Cross-platform sound notification system for IBKRBot.
Works on Windows, macOS, and Linux.
"""
from __future__ import annotations
import sys
import logging
from pathlib import Path
from typing import Optional

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


class SoundPlayer:
    """Cross-platform sound player using Qt's QSound or system beeps."""

    _instance: Optional['SoundPlayer'] = None
    _enabled: bool = True

    def __new__(cls) -> 'SoundPlayer':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._qt_available = False
        self._sounds_dir: Optional[Path] = None

        # Try to import Qt multimedia
        try:
            from PySide6.QtCore import QUrl
            from PySide6.QtMultimedia import QSoundEffect
            self._qt_available = True
            self._sound_effects: dict = {}
            _log.debug("Qt multimedia available for sound playback")
        except ImportError:
            _log.warning("Qt multimedia not available, using system beeps")

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        _log.info(f"Sound notifications {'enabled' if value else 'disabled'}")

    def play(self, sound_type: str = SOUND_ALERT) -> None:
        """Play a sound notification."""
        if not self._enabled:
            return

        try:
            if self._qt_available:
                self._play_qt_sound(sound_type)
            else:
                self._play_system_beep(sound_type)
        except Exception as e:
            _log.debug(f"Could not play sound: {e}")

    def _play_qt_sound(self, sound_type: str) -> None:
        """Play sound using Qt (cross-platform)."""
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QTimer

            # Use system bell as fallback - simple and cross-platform
            app = QApplication.instance()
            if app:
                app.beep()
        except Exception as e:
            _log.debug(f"Qt sound failed: {e}")
            self._play_system_beep(sound_type)

    def _play_system_beep(self, sound_type: str) -> None:
        """Play system beep (fallback)."""
        try:
            if sys.platform == "win32":
                import winsound
                # Different frequencies for different sounds
                freq_map = {
                    SOUND_SUCCESS: (1000, 200),
                    SOUND_ERROR: (400, 500),
                    SOUND_WARNING: (600, 300),
                    SOUND_ORDER_FILLED: (1200, 300),
                    SOUND_ORDER_PLACED: (800, 200),
                    SOUND_ALERT: (1000, 400),
                    SOUND_CONNECT: (1500, 200),
                    SOUND_DISCONNECT: (300, 400),
                }
                freq, duration = freq_map.get(sound_type, (1000, 200))
                winsound.Beep(freq, duration)
            else:
                # macOS and Linux - print bell character
                print('\a', end='', flush=True)
        except Exception as e:
            _log.debug(f"System beep failed: {e}")

    def play_success(self) -> None:
        """Play success sound."""
        self.play(SOUND_SUCCESS)

    def play_error(self) -> None:
        """Play error sound."""
        self.play(SOUND_ERROR)

    def play_warning(self) -> None:
        """Play warning sound."""
        self.play(SOUND_WARNING)

    def play_order_filled(self) -> None:
        """Play order filled sound."""
        self.play(SOUND_ORDER_FILLED)

    def play_order_placed(self) -> None:
        """Play order placed sound."""
        self.play(SOUND_ORDER_PLACED)

    def play_alert(self) -> None:
        """Play alert sound."""
        self.play(SOUND_ALERT)

    def play_connect(self) -> None:
        """Play connection sound."""
        self.play(SOUND_CONNECT)

    def play_disconnect(self) -> None:
        """Play disconnection sound."""
        self.play(SOUND_DISCONNECT)


# Global instance
_player: Optional[SoundPlayer] = None


def get_sound_player() -> SoundPlayer:
    """Get the global sound player instance."""
    global _player
    if _player is None:
        _player = SoundPlayer()
    return _player


def play_sound(sound_type: str = SOUND_ALERT) -> None:
    """Play a sound notification."""
    get_sound_player().play(sound_type)


def set_sound_enabled(enabled: bool) -> None:
    """Enable or disable sound notifications."""
    get_sound_player().enabled = enabled


def is_sound_enabled() -> bool:
    """Check if sound notifications are enabled."""
    return get_sound_player().enabled
