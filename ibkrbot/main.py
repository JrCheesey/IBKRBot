from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication
from ibkrbot.core.logging_setup import setup_logging
from ibkrbot.ui.main_window import MainWindow
from ibkrbot.ui.theme import Spacing

def main() -> int:
    logger = setup_logging()
    app = QApplication(sys.argv)

    # Apply light theme by default to override system dark mode
    from ibkrbot.ui.theme import apply_theme, ThemeMode
    apply_theme(ThemeMode.LIGHT)

    w = MainWindow(logger=logger)
    w.resize(Spacing.MAIN_WINDOW_WIDTH, Spacing.MAIN_WINDOW_HEIGHT)
    w.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
