"""
UI theme and styling constants for IBKRBot.
Centralizes all colors, fonts, and style definitions.
"""

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
