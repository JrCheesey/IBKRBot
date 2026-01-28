"""
Watchlist Widget for IBKRBot.
Displays a list of symbols with real-time price updates.
"""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
import threading
import time

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
        QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
        QLineEdit, QMessageBox, QMenu
    )
    from PySide6.QtCore import Qt, Signal, QTimer
    from PySide6.QtGui import QFont, QColor, QAction
    _qt_available = True
except ImportError:
    _qt_available = False


if _qt_available:
    class WatchlistWidget(QWidget):
        """Widget displaying a watchlist of symbols with prices."""

        symbol_selected = Signal(str)  # Emitted when user clicks a symbol
        symbol_added = Signal(str)
        symbol_removed = Signal(str)

        def __init__(self, parent=None):
            super().__init__(parent)
            self._symbols: List[str] = []
            self._prices: Dict[str, Dict[str, Any]] = {}  # symbol -> {price, change, change_pct, ...}
            self._price_fetcher: Optional[Callable[[str], Optional[Dict[str, Any]]]] = None
            self._update_timer: Optional[QTimer] = None
            self._update_interval_ms = 60000  # Default 1 minute

            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout()
            layout.setSpacing(8)

            # Header with add symbol input
            header = QHBoxLayout()
            header.addWidget(QLabel("Watchlist"))
            header.addStretch()

            self.add_input = QLineEdit()
            self.add_input.setPlaceholderText("Add symbol...")
            self.add_input.setMaximumWidth(100)
            self.add_input.returnPressed.connect(self._on_add_symbol)
            header.addWidget(self.add_input)

            self.add_btn = QPushButton("+")
            self.add_btn.setMaximumWidth(30)
            self.add_btn.clicked.connect(self._on_add_symbol)
            header.addWidget(self.add_btn)

            layout.addLayout(header)

            # Watchlist table
            self.table = QTableWidget(0, 5)
            self.table.setHorizontalHeaderLabels([
                "Symbol", "Price", "Change", "Change %", "Last Update"
            ])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.setAlternatingRowColors(True)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            self.table.setContextMenuPolicy(Qt.CustomContextMenu)
            self.table.customContextMenuRequested.connect(self._show_context_menu)
            self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

            layout.addWidget(self.table)

            # Status row
            status_row = QHBoxLayout()
            self.status_label = QLabel("0 symbols")
            self.status_label.setStyleSheet("color: #666; font-size: 10px;")
            status_row.addWidget(self.status_label)

            status_row.addStretch()

            self.refresh_btn = QPushButton("Refresh")
            self.refresh_btn.setMaximumWidth(80)
            self.refresh_btn.clicked.connect(self.refresh_prices)
            status_row.addWidget(self.refresh_btn)

            layout.addLayout(status_row)

            self.setLayout(layout)

        def set_symbols(self, symbols: List[str]):
            """Set the list of symbols to watch."""
            self._symbols = [s.upper() for s in symbols]
            self._update_table()

        def add_symbol(self, symbol: str) -> bool:
            """Add a symbol to the watchlist."""
            symbol = symbol.upper().strip()
            if not symbol:
                return False
            if symbol in self._symbols:
                return False

            self._symbols.append(symbol)
            self._update_table()
            self.symbol_added.emit(symbol)
            return True

        def remove_symbol(self, symbol: str) -> bool:
            """Remove a symbol from the watchlist."""
            symbol = symbol.upper()
            if symbol not in self._symbols:
                return False

            self._symbols.remove(symbol)
            if symbol in self._prices:
                del self._prices[symbol]
            self._update_table()
            self.symbol_removed.emit(symbol)
            return True

        def set_price_fetcher(self, fetcher: Callable[[str], Optional[Dict[str, Any]]]):
            """
            Set the function used to fetch price data.

            The fetcher should return a dict with keys:
            - price: float
            - change: float (optional)
            - change_pct: float (optional)
            - high: float (optional)
            - low: float (optional)
            - volume: int (optional)
            """
            self._price_fetcher = fetcher

        def start_auto_update(self, interval_ms: int = 60000):
            """Start automatic price updates."""
            self._update_interval_ms = interval_ms

            if self._update_timer is None:
                self._update_timer = QTimer()
                self._update_timer.timeout.connect(self.refresh_prices)

            self._update_timer.start(interval_ms)

        def stop_auto_update(self):
            """Stop automatic price updates."""
            if self._update_timer:
                self._update_timer.stop()

        def refresh_prices(self):
            """Refresh all prices."""
            if not self._price_fetcher:
                return

            for symbol in self._symbols:
                try:
                    data = self._price_fetcher(symbol)
                    if data:
                        data['last_update'] = datetime.now().strftime("%H:%M:%S")
                        self._prices[symbol] = data
                except Exception:
                    pass

            self._update_table()

        def update_price(self, symbol: str, price_data: Dict[str, Any]):
            """Update price for a single symbol."""
            symbol = symbol.upper()
            if symbol not in self._symbols:
                return

            price_data['last_update'] = datetime.now().strftime("%H:%M:%S")
            self._prices[symbol] = price_data
            self._update_table()

        def _update_table(self):
            """Update the table display."""
            self.table.setRowCount(0)
            self.table.setRowCount(len(self._symbols))

            for row, symbol in enumerate(self._symbols):
                data = self._prices.get(symbol, {})

                price = data.get('price', '--')
                change = data.get('change', 0)
                change_pct = data.get('change_pct', 0)
                last_update = data.get('last_update', '--')

                # Format values
                price_str = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
                change_str = f"{change:+.2f}" if isinstance(change, (int, float)) else "--"
                change_pct_str = f"{change_pct:+.2f}%" if isinstance(change_pct, (int, float)) else "--"

                items = [
                    QTableWidgetItem(symbol),
                    QTableWidgetItem(price_str),
                    QTableWidgetItem(change_str),
                    QTableWidgetItem(change_pct_str),
                    QTableWidgetItem(last_update),
                ]

                # Color-code change columns
                if isinstance(change, (int, float)):
                    color = QColor("#0a0") if change >= 0 else QColor("#b00")
                    items[2].setForeground(color)
                    items[3].setForeground(color)

                # Bold symbol
                font = items[0].font()
                font.setBold(True)
                items[0].setFont(font)

                for col, item in enumerate(items):
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)

            self.status_label.setText(f"{len(self._symbols)} symbols")

        def _on_add_symbol(self):
            """Handle add symbol button/enter."""
            symbol = self.add_input.text().strip().upper()
            if symbol:
                if self.add_symbol(symbol):
                    self.add_input.clear()
                else:
                    QMessageBox.warning(self, "Already in Watchlist", f"{symbol} is already in the watchlist.")

        def _on_cell_double_clicked(self, row: int, col: int):
            """Handle double-click on a cell."""
            if row < len(self._symbols):
                symbol = self._symbols[row]
                self.symbol_selected.emit(symbol)

        def _show_context_menu(self, pos):
            """Show context menu for table."""
            row = self.table.rowAt(pos.y())
            if row < 0 or row >= len(self._symbols):
                return

            symbol = self._symbols[row]
            menu = QMenu(self)

            select_action = QAction(f"Select {symbol}", self)
            select_action.triggered.connect(lambda: self.symbol_selected.emit(symbol))
            menu.addAction(select_action)

            menu.addSeparator()

            remove_action = QAction(f"Remove {symbol}", self)
            remove_action.triggered.connect(lambda: self.remove_symbol(symbol))
            menu.addAction(remove_action)

            menu.exec(self.table.mapToGlobal(pos))

        def get_symbols(self) -> List[str]:
            """Get the current list of symbols."""
            return self._symbols.copy()
else:
    # Stub class when Qt is not available
    class WatchlistWidget:
        def __init__(self, parent=None):
            pass
