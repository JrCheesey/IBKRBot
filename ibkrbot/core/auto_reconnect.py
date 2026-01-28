"""
Auto-reconnect logic for IBKRBot.
Handles automatic reconnection to IB Gateway when connection is lost.
"""
from __future__ import annotations
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Optional

_log = logging.getLogger(__name__)


@dataclass
class ReconnectConfig:
    """Configuration for auto-reconnect behavior."""
    enabled: bool = True
    max_attempts: int = 5
    initial_delay_seconds: float = 5.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    reset_after_success_seconds: float = 300.0  # Reset attempt counter after 5 min of stable connection


class AutoReconnectManager:
    """Manages automatic reconnection to IB Gateway."""

    def __init__(self, config: Optional[ReconnectConfig] = None):
        self._config = config or ReconnectConfig()
        self._attempt_count = 0
        self._last_success: Optional[datetime] = None
        self._last_disconnect: Optional[datetime] = None
        self._running = False
        self._reconnect_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Callbacks
        self._connect_callback: Optional[Callable[[], bool]] = None
        self._is_connected_callback: Optional[Callable[[], bool]] = None
        self._on_reconnect_start: Optional[Callable[[], None]] = None
        self._on_reconnect_success: Optional[Callable[[], None]] = None
        self._on_reconnect_failed: Optional[Callable[[int], None]] = None
        self._on_reconnect_exhausted: Optional[Callable[[], None]] = None

    @property
    def config(self) -> ReconnectConfig:
        return self._config

    @config.setter
    def config(self, value: ReconnectConfig) -> None:
        self._config = value

    @property
    def attempt_count(self) -> int:
        return self._attempt_count

    @property
    def is_reconnecting(self) -> bool:
        return self._reconnect_thread is not None and self._reconnect_thread.is_alive()

    def set_callbacks(
        self,
        connect: Callable[[], bool],
        is_connected: Callable[[], bool],
        on_start: Optional[Callable[[], None]] = None,
        on_success: Optional[Callable[[], None]] = None,
        on_failed: Optional[Callable[[int], None]] = None,
        on_exhausted: Optional[Callable[[], None]] = None,
    ) -> None:
        """
        Set the callbacks for reconnection.

        Args:
            connect: Function that attempts to connect, returns True on success
            is_connected: Function that checks if currently connected
            on_start: Called when reconnection attempt starts
            on_success: Called when reconnection succeeds
            on_failed: Called when a reconnection attempt fails (passed attempt count)
            on_exhausted: Called when all reconnection attempts are exhausted
        """
        self._connect_callback = connect
        self._is_connected_callback = is_connected
        self._on_reconnect_start = on_start
        self._on_reconnect_success = on_success
        self._on_reconnect_failed = on_failed
        self._on_reconnect_exhausted = on_exhausted

    def on_connection_lost(self) -> None:
        """Called when connection is detected as lost."""
        if not self._config.enabled:
            _log.info("Auto-reconnect disabled, not attempting reconnection")
            return

        self._last_disconnect = datetime.now(timezone.utc)

        # Check if already reconnecting
        if self.is_reconnecting:
            _log.debug("Already reconnecting, ignoring duplicate disconnect event")
            return

        # Check if we've reset the counter due to stable connection
        if self._last_success:
            seconds_since_success = (datetime.now(timezone.utc) - self._last_success).total_seconds()
            if seconds_since_success > self._config.reset_after_success_seconds:
                _log.debug("Resetting attempt counter due to previous stable connection")
                self._attempt_count = 0

        _log.info("Connection lost, starting auto-reconnect")
        self._start_reconnect()

    def on_connection_success(self) -> None:
        """Called when connection is successfully established."""
        with self._lock:
            self._last_success = datetime.now(timezone.utc)
            self._attempt_count = 0
        _log.debug("Connection successful, reset attempt counter")

    def stop(self) -> None:
        """Stop any ongoing reconnection attempts."""
        self._running = False
        if self._reconnect_thread:
            self._reconnect_thread.join(timeout=2.0)
            self._reconnect_thread = None

    def reset(self) -> None:
        """Reset the reconnection state."""
        self.stop()
        with self._lock:
            self._attempt_count = 0
            self._last_success = None
            self._last_disconnect = None

    def _start_reconnect(self) -> None:
        """Start the reconnection process in a background thread."""
        self._running = True
        self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self._reconnect_thread.start()

    def _reconnect_loop(self) -> None:
        """Background thread that handles reconnection attempts."""
        if self._on_reconnect_start:
            try:
                self._on_reconnect_start()
            except Exception as e:
                _log.error(f"Error in on_reconnect_start callback: {e}")

        delay = self._config.initial_delay_seconds

        while self._running and self._attempt_count < self._config.max_attempts:
            # Check if already connected
            if self._is_connected_callback and self._is_connected_callback():
                _log.info("Already connected, stopping reconnect")
                self._running = False
                break

            with self._lock:
                self._attempt_count += 1
                current_attempt = self._attempt_count

            _log.info(f"Reconnection attempt {current_attempt}/{self._config.max_attempts} in {delay:.1f}s")

            # Wait before attempting
            self._interruptible_sleep(delay)

            if not self._running:
                break

            # Check connection again before attempting
            if self._is_connected_callback and self._is_connected_callback():
                _log.info("Connected during wait, stopping reconnect")
                self._running = False
                break

            # Attempt connection
            success = False
            if self._connect_callback:
                try:
                    success = self._connect_callback()
                except Exception as e:
                    _log.warning(f"Reconnection attempt {current_attempt} failed: {e}")
                    success = False

            if success:
                _log.info("Reconnection successful!")
                self._running = False
                self.on_connection_success()

                if self._on_reconnect_success:
                    try:
                        self._on_reconnect_success()
                    except Exception as e:
                        _log.error(f"Error in on_reconnect_success callback: {e}")
                break
            else:
                _log.warning(f"Reconnection attempt {current_attempt} failed")

                if self._on_reconnect_failed:
                    try:
                        self._on_reconnect_failed(current_attempt)
                    except Exception as e:
                        _log.error(f"Error in on_reconnect_failed callback: {e}")

                # Increase delay with backoff
                delay = min(delay * self._config.backoff_multiplier, self._config.max_delay_seconds)

        # Check if we exhausted all attempts
        if self._running and self._attempt_count >= self._config.max_attempts:
            _log.error(f"All {self._config.max_attempts} reconnection attempts exhausted")
            self._running = False

            if self._on_reconnect_exhausted:
                try:
                    self._on_reconnect_exhausted()
                except Exception as e:
                    _log.error(f"Error in on_reconnect_exhausted callback: {e}")

    def _interruptible_sleep(self, seconds: float) -> None:
        """Sleep that can be interrupted by stopping."""
        end_time = time.time() + seconds
        while time.time() < end_time and self._running:
            time.sleep(min(0.5, end_time - time.time()))


# Global instance
_reconnect_manager: Optional[AutoReconnectManager] = None


def get_reconnect_manager() -> AutoReconnectManager:
    """Get the global auto-reconnect manager instance."""
    global _reconnect_manager
    if _reconnect_manager is None:
        _reconnect_manager = AutoReconnectManager()
    return _reconnect_manager
