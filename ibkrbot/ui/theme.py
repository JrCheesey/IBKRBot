"""
UI theme and styling constants for IBKRBot.
Centralizes all colors, fonts, and style definitions.
Supports light and dark themes.
"""
from __future__ import annotations
from enum import Enum
from typing import Optional


class ThemeMode(Enum):
    """Available theme modes."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"  # Follow system preference


class Colors:
    """Color palette for the application (Light Theme)"""
    # Status colors
    SUCCESS = "#0a0"           # Green for success/connected
    ERROR = "#b00"             # Red for errors/disconnected
    WARNING = "#856404"        # Brown for warnings
    INFO = "#084298"           # Blue for info

    # Text colors
    TEXT_PRIMARY = "#333"      # Primary text
    TEXT_SECONDARY = "#666"    # Secondary/muted text
    TEXT_HINT = "#555"         # Hint text
    TEXT_DISABLED = "#999"     # Disabled text

    # Background colors
    BG_WARNING = "#fff3cd"     # Warning background
    BG_WARNING_BORDER = "#ffeeba"
    BG_ERROR = "#f8d7da"       # Error background
    BG_ERROR_BORDER = "#f5c2c7"
    BG_INFO = "#eef5ff"        # Info background
    BG_INFO_BORDER = "#cfe2ff"

    # Border colors
    BORDER_LIGHT = "#ddd"      # Light borders
    BORDER_MEDIUM = "#ccc"     # Medium borders
    BORDER_DARK = "#999"       # Dark borders


class ColorsDark:
    """Dark theme color palette (for future implementation)"""
    # Status colors
    SUCCESS = "#0f0"
    ERROR = "#f55"
    WARNING = "#fa5"
    INFO = "#59f"

    # Text colors
    TEXT_PRIMARY = "#e0e0e0"
    TEXT_SECONDARY = "#aaa"
    TEXT_HINT = "#888"
    TEXT_DISABLED = "#666"

    # Background colors
    BG_WARNING = "#332800"
    BG_WARNING_BORDER = "#554400"
    BG_ERROR = "#330808"
    BG_ERROR_BORDER = "#551010"
    BG_INFO = "#001a33"
    BG_INFO_BORDER = "#003366"

    # Border colors
    BORDER_LIGHT = "#444"
    BORDER_MEDIUM = "#555"
    BORDER_DARK = "#666"


class Fonts:
    """Font settings for the application"""
    SIZE_TITLE = 13           # Workflow titles, section headers
    SIZE_BODY = 10            # Normal text
    SIZE_SMALL = 9            # Small text, hints


class Spacing:
    """Spacing and sizing constants"""
    PADDING_SMALL = 4
    PADDING_MEDIUM = 8
    PADDING_LARGE = 12

    BORDER_RADIUS = 6

    # Window sizes
    MAIN_WINDOW_WIDTH = 1200
    MAIN_WINDOW_HEIGHT = 800

    DIALOG_WIDTH_SMALL = 520
    DIALOG_WIDTH_MEDIUM = 740
    DIALOG_WIDTH_LARGE = 800
    DIALOG_HEIGHT_STANDARD = 520


class Styles:
    """Pre-built style strings for common UI patterns"""

    @staticmethod
    def secondary_text() -> str:
        """Style for secondary/muted text"""
        return f"color: {Colors.TEXT_SECONDARY};"

    @staticmethod
    def hint_text() -> str:
        """Style for hint text"""
        return f"color: {Colors.TEXT_HINT};"

    @staticmethod
    def workflow_step() -> str:
        """Style for workflow step labels"""
        return f"color: {Colors.TEXT_PRIMARY};"

    @staticmethod
    def workflow_next_box() -> str:
        """Style for 'Next:' suggestion box"""
        return (
            f"margin-top: {Spacing.PADDING_MEDIUM}px; "
            f"padding: {Spacing.PADDING_MEDIUM}px; "
            f"border-radius: {Spacing.BORDER_RADIUS}px; "
            f"background: {Colors.BG_INFO}; "
            f"border: 1px solid {Colors.BG_INFO_BORDER}; "
            f"color: {Colors.INFO};"
        )

    @staticmethod
    def warning_banner() -> str:
        """Style for warning banners"""
        return (
            f"padding: {Spacing.PADDING_MEDIUM}px; "
            f"border-radius: {Spacing.BORDER_RADIUS}px; "
            f"background: {Colors.BG_WARNING}; "
            f"border: 1px solid {Colors.BG_WARNING_BORDER}; "
            f"color: {Colors.WARNING};"
        )

    @staticmethod
    def error_banner() -> str:
        """Style for error banners"""
        return (
            f"padding: {Spacing.PADDING_MEDIUM}px; "
            f"border-radius: {Spacing.BORDER_RADIUS}px; "
            f"background: {Colors.BG_ERROR}; "
            f"border: 1px solid {Colors.BG_ERROR_BORDER}; "
            f"color: {Colors.ERROR};"
        )

    @staticmethod
    def chart_border() -> str:
        """Style for chart thumbnail border"""
        return (
            f"border: 1px solid {Colors.BORDER_LIGHT}; "
            f"border-radius: {Spacing.BORDER_RADIUS}px; "
            f"padding: {Spacing.PADDING_SMALL}px; "
            f"color: {Colors.TEXT_SECONDARY};"
        )

    @staticmethod
    def connection_dot_connected() -> str:
        """Style for connection status dot (connected)"""
        return f"color: {Colors.SUCCESS};"

    @staticmethod
    def connection_dot_disconnected() -> str:
        """Style for connection status dot (disconnected)"""
        return f"color: {Colors.ERROR};"

    @staticmethod
    def unsaved_warning() -> str:
        """Style for unsaved changes warning"""
        return f"color: {Colors.ERROR};"


class StylesDark:
    """Pre-built style strings for dark theme."""

    @staticmethod
    def secondary_text() -> str:
        return f"color: {ColorsDark.TEXT_SECONDARY};"

    @staticmethod
    def hint_text() -> str:
        return f"color: {ColorsDark.TEXT_HINT};"

    @staticmethod
    def workflow_step() -> str:
        return f"color: {ColorsDark.TEXT_PRIMARY};"

    @staticmethod
    def workflow_next_box() -> str:
        return (
            f"margin-top: {Spacing.PADDING_MEDIUM}px; "
            f"padding: {Spacing.PADDING_MEDIUM}px; "
            f"border-radius: {Spacing.BORDER_RADIUS}px; "
            f"background: {ColorsDark.BG_INFO}; "
            f"border: 1px solid {ColorsDark.BG_INFO_BORDER}; "
            f"color: {ColorsDark.INFO};"
        )

    @staticmethod
    def warning_banner() -> str:
        return (
            f"padding: {Spacing.PADDING_MEDIUM}px; "
            f"border-radius: {Spacing.BORDER_RADIUS}px; "
            f"background: {ColorsDark.BG_WARNING}; "
            f"border: 1px solid {ColorsDark.BG_WARNING_BORDER}; "
            f"color: {ColorsDark.WARNING};"
        )

    @staticmethod
    def error_banner() -> str:
        return (
            f"padding: {Spacing.PADDING_MEDIUM}px; "
            f"border-radius: {Spacing.BORDER_RADIUS}px; "
            f"background: {ColorsDark.BG_ERROR}; "
            f"border: 1px solid {ColorsDark.BG_ERROR_BORDER}; "
            f"color: {ColorsDark.ERROR};"
        )

    @staticmethod
    def chart_border() -> str:
        return (
            f"border: 1px solid {ColorsDark.BORDER_LIGHT}; "
            f"border-radius: {Spacing.BORDER_RADIUS}px; "
            f"padding: {Spacing.PADDING_SMALL}px; "
            f"color: {ColorsDark.TEXT_SECONDARY};"
        )

    @staticmethod
    def connection_dot_connected() -> str:
        return f"color: {ColorsDark.SUCCESS};"

    @staticmethod
    def connection_dot_disconnected() -> str:
        return f"color: {ColorsDark.ERROR};"

    @staticmethod
    def unsaved_warning() -> str:
        return f"color: {ColorsDark.ERROR};"


class ThemeManager:
    """Manages the application theme."""

    _instance: Optional['ThemeManager'] = None
    _current_mode: ThemeMode = ThemeMode.LIGHT

    def __new__(cls) -> 'ThemeManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def mode(self) -> ThemeMode:
        return self._current_mode

    @mode.setter
    def mode(self, value: ThemeMode) -> None:
        self._current_mode = value

    @property
    def is_dark(self) -> bool:
        if self._current_mode == ThemeMode.SYSTEM:
            return self._detect_system_dark_mode()
        return self._current_mode == ThemeMode.DARK

    def _detect_system_dark_mode(self) -> bool:
        """Detect if system is using dark mode."""
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtGui import QPalette

            app = QApplication.instance()
            if app:
                palette = app.palette()
                bg_color = palette.color(QPalette.Window)
                # If background is dark, we're in dark mode
                return bg_color.lightness() < 128
        except Exception:
            pass
        return False

    @property
    def colors(self):
        """Get the current color palette."""
        return ColorsDark if self.is_dark else Colors

    @property
    def styles(self):
        """Get the current styles class."""
        return StylesDark if self.is_dark else Styles

    def get_dark_mode_stylesheet(self) -> str:
        """Get a complete dark mode stylesheet for the application."""
        return """
            QMainWindow, QDialog, QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }

            QLabel {
                color: #e0e0e0;
            }

            QPushButton {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 6px 12px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #4a4a4a;
            }

            QPushButton:pressed {
                background-color: #2a2a2a;
            }

            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666;
            }

            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
                border-radius: 3px;
            }

            QComboBox {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
                border-radius: 3px;
            }

            QComboBox::drop-down {
                border-left: 1px solid #555;
            }

            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: #e0e0e0;
                selection-background-color: #3a5f8a;
            }

            QGroupBox {
                border: 1px solid #555;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
                color: #e0e0e0;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }

            QTableWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
                gridline-color: #444;
                border: 1px solid #555;
            }

            QTableWidget::item {
                padding: 4px;
            }

            QTableWidget::item:selected {
                background-color: #3a5f8a;
            }

            QHeaderView::section {
                background-color: #3c3c3c;
                color: #e0e0e0;
                padding: 4px;
                border: 1px solid #555;
            }

            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #666;
            }

            QScrollBar:horizontal {
                background-color: #2d2d2d;
                height: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:horizontal {
                background-color: #555;
                border-radius: 6px;
                min-width: 20px;
            }

            QProgressBar {
                background-color: #2d2d2d;
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
                color: #e0e0e0;
            }

            QProgressBar::chunk {
                background-color: #3a5f8a;
                border-radius: 3px;
            }

            QMenuBar {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }

            QMenuBar::item:selected {
                background-color: #3a5f8a;
            }

            QMenu {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555;
            }

            QMenu::item:selected {
                background-color: #3a5f8a;
            }

            QStatusBar {
                background-color: #2d2d2d;
                color: #e0e0e0;
            }

            QToolTip {
                background-color: #3c3c3c;
                color: #e0e0e0;
                border: 1px solid #555;
                padding: 4px;
            }

            QSplitter::handle {
                background-color: #444;
            }

            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #1e1e1e;
            }

            QTabBar::tab {
                background-color: #2d2d2d;
                color: #e0e0e0;
                padding: 8px 16px;
                border: 1px solid #555;
            }

            QTabBar::tab:selected {
                background-color: #3c3c3c;
            }

            QCheckBox, QRadioButton {
                color: #e0e0e0;
            }
        """

    def get_light_mode_stylesheet(self) -> str:
        """Get a complete light mode stylesheet (essentially reset to defaults)."""
        return ""  # Return empty to use Qt defaults

    def get_current_stylesheet(self) -> str:
        """Get stylesheet for current theme mode."""
        if self.is_dark:
            return self.get_dark_mode_stylesheet()
        return self.get_light_mode_stylesheet()


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def apply_theme(mode: ThemeMode) -> None:
    """Apply a theme to the application."""
    try:
        from PySide6.QtWidgets import QApplication

        manager = get_theme_manager()
        manager.mode = mode

        app = QApplication.instance()
        if app:
            app.setStyleSheet(manager.get_current_stylesheet())
    except Exception:
        pass


def toggle_dark_mode() -> bool:
    """Toggle between light and dark mode. Returns True if now dark."""
    manager = get_theme_manager()
    new_mode = ThemeMode.LIGHT if manager.is_dark else ThemeMode.DARK
    apply_theme(new_mode)
    return manager.is_dark
