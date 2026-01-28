"""
System tray support for IBKRBot.
Allows the application to minimize to system tray with notifications.
"""
from __future__ import annotations
import logging
import sys
from typing import Callable, Optional

_log = logging.getLogger(__name__)

# Qt imports are done conditionally to support headless environments
_qt_available = False
try:
    from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
    from PySide6.QtGui import QIcon, QAction
    from PySide6.QtCore import QObject, Signal
    _qt_available = True
except ImportError:
    _log.debug("PySide6 not available for system tray")


class TrayIconManager:
    """Manages the system tray icon and notifications."""

    def __init__(self, app_name: str = "IBKRBot"):
        self._app_name = app_name
        self._tray_icon: Optional[QSystemTrayIcon] = None
        self._menu: Optional[QMenu] = None
        self._main_window = None
        self._show_callback: Optional[Callable] = None
        self._quit_callback: Optional[Callable] = None
        self._minimize_to_tray = True

    @property
    def is_available(self) -> bool:
        """Check if system tray is available."""
        if not _qt_available:
            return False
        return QSystemTrayIcon.isSystemTrayAvailable()

    def setup(self, main_window, icon_path: Optional[str] = None) -> bool:
        """
        Setup the system tray icon.

        Args:
            main_window: The main application window
            icon_path: Optional path to icon file

        Returns:
            True if setup successful
        """
        if not self.is_available:
            _log.warning("System tray not available on this system")
            return False

        self._main_window = main_window

        # Create tray icon
        self._tray_icon = QSystemTrayIcon(main_window)

        # Set icon
        if icon_path:
            icon = QIcon(icon_path)
        else:
            # Use application icon or default
            app = QApplication.instance()
            if app and not app.windowIcon().isNull():
                icon = app.windowIcon()
            else:
                # Create a simple default icon
                icon = QIcon()

        self._tray_icon.setIcon(icon)
        self._tray_icon.setToolTip(self._app_name)

        # Create context menu
        self._menu = QMenu()

        # Show/Hide action
        show_action = QAction("Show Window", self._menu)
        show_action.triggered.connect(self._on_show_window)
        self._menu.addAction(show_action)

        self._menu.addSeparator()

        # Status indicator (read-only)
        self._status_action = QAction("Status: Disconnected", self._menu)
        self._status_action.setEnabled(False)
        self._menu.addAction(self._status_action)

        self._menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self._menu)
        quit_action.triggered.connect(self._on_quit)
        self._menu.addAction(quit_action)

        self._tray_icon.setContextMenu(self._menu)

        # Connect signals
        self._tray_icon.activated.connect(self._on_tray_activated)

        _log.info("System tray icon setup complete")
        return True

    def show(self) -> None:
        """Show the tray icon."""
        if self._tray_icon:
            self._tray_icon.show()

    def hide(self) -> None:
        """Hide the tray icon."""
        if self._tray_icon:
            self._tray_icon.hide()

    def set_status(self, status: str) -> None:
        """Update the status text in the tray menu."""
        if self._status_action:
            self._status_action.setText(f"Status: {status}")

    def set_tooltip(self, tooltip: str) -> None:
        """Set the tray icon tooltip."""
        if self._tray_icon:
            self._tray_icon.setToolTip(tooltip)

    def show_notification(self, title: str, message: str,
                         icon_type: str = "info", duration_ms: int = 5000) -> None:
        """
        Show a system notification.

        Args:
            title: Notification title
            message: Notification message
            icon_type: "info", "warning", or "error"
            duration_ms: Duration in milliseconds
        """
        if not self._tray_icon:
            return

        # Map icon type to Qt icon
        icon_map = {
            "info": QSystemTrayIcon.Information,
            "warning": QSystemTrayIcon.Warning,
            "error": QSystemTrayIcon.Critical,
        }
        icon = icon_map.get(icon_type, QSystemTrayIcon.Information)

        self._tray_icon.showMessage(title, message, icon, duration_ms)
        _log.debug(f"Tray notification: {title} - {message}")

    def set_show_callback(self, callback: Callable) -> None:
        """Set callback for show window action."""
        self._show_callback = callback

    def set_quit_callback(self, callback: Callable) -> None:
        """Set callback for quit action."""
        self._quit_callback = callback

    def set_minimize_to_tray(self, enabled: bool) -> None:
        """Enable/disable minimize to tray behavior."""
        self._minimize_to_tray = enabled

    @property
    def minimize_to_tray_enabled(self) -> bool:
        """Check if minimize to tray is enabled."""
        return self._minimize_to_tray and self.is_available

    def _on_show_window(self) -> None:
        """Handle show window action."""
        if self._show_callback:
            self._show_callback()
        elif self._main_window:
            self._main_window.show()
            self._main_window.raise_()
            self._main_window.activateWindow()

    def _on_quit(self) -> None:
        """Handle quit action."""
        if self._quit_callback:
            self._quit_callback()
        elif self._main_window:
            self._main_window.close()

    def _on_tray_activated(self, reason) -> None:
        """Handle tray icon activation (click)."""
        if reason == QSystemTrayIcon.DoubleClick:
            self._on_show_window()
        elif reason == QSystemTrayIcon.Trigger:
            # Single click - toggle window visibility
            if self._main_window:
                if self._main_window.isVisible():
                    self._main_window.hide()
                else:
                    self._on_show_window()


# Global instance
_tray_manager: Optional[TrayIconManager] = None


def get_tray_manager() -> TrayIconManager:
    """Get the global tray manager instance."""
    global _tray_manager
    if _tray_manager is None:
        _tray_manager = TrayIconManager()
    return _tray_manager
