"""
Portfolio Summary Widget for IBKRBot.
Displays account summary, positions, and P&L at a glance.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
        QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
        QFrame
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QFont, QColor
    _qt_available = True
except ImportError:
    _qt_available = False


if _qt_available:
    class PortfolioWidget(QWidget):
        """Widget displaying portfolio summary and positions."""

        refresh_requested = Signal()

        def __init__(self, parent=None):
            super().__init__(parent)
            self._net_liq: float = 0.0
            self._buying_power: float = 0.0
            self._cash: float = 0.0
            self._positions: List[Dict[str, Any]] = []
            self._total_pnl: float = 0.0
            self._daily_pnl: float = 0.0

            self._setup_ui()

        def _setup_ui(self):
            layout = QVBoxLayout()
            layout.setSpacing(8)

            # Account Summary Section
            summary_box = QGroupBox("Account Summary")
            summary_layout = QVBoxLayout()

            # Net Liquidation Value
            self.netliq_label = QLabel("Net Liquidation: --")
            self.netliq_label.setFont(QFont("", 12, QFont.Bold))
            summary_layout.addWidget(self.netliq_label)

            # Row with buying power and cash
            row1 = QHBoxLayout()
            self.buying_power_label = QLabel("Buying Power: --")
            self.cash_label = QLabel("Cash: --")
            row1.addWidget(self.buying_power_label)
            row1.addWidget(self.cash_label)
            row1.addStretch()
            summary_layout.addLayout(row1)

            # P&L Row
            row2 = QHBoxLayout()
            self.daily_pnl_label = QLabel("Daily P&L: --")
            self.total_pnl_label = QLabel("Total P&L: --")
            row2.addWidget(self.daily_pnl_label)
            row2.addWidget(self.total_pnl_label)
            row2.addStretch()
            summary_layout.addLayout(row2)

            summary_box.setLayout(summary_layout)
            layout.addWidget(summary_box)

            # Positions Section
            positions_box = QGroupBox("Open Positions")
            positions_layout = QVBoxLayout()

            # Position count label
            self.position_count_label = QLabel("No open positions")
            positions_layout.addWidget(self.position_count_label)

            # Positions table
            self.positions_table = QTableWidget(0, 6)
            self.positions_table.setHorizontalHeaderLabels([
                "Symbol", "Qty", "Avg Cost", "Current", "P&L", "P&L %"
            ])
            self.positions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.positions_table.setAlternatingRowColors(True)
            self.positions_table.setMaximumHeight(200)
            positions_layout.addWidget(self.positions_table)

            positions_box.setLayout(positions_layout)
            layout.addWidget(positions_box)

            # Exposure Bar
            exposure_box = QGroupBox("Portfolio Exposure")
            exposure_layout = QVBoxLayout()

            self.exposure_bar = QProgressBar()
            self.exposure_bar.setRange(0, 100)
            self.exposure_bar.setValue(0)
            self.exposure_bar.setFormat("Invested: 0%")
            exposure_layout.addWidget(self.exposure_bar)

            self.exposure_detail = QLabel("Cash: -- | Invested: --")
            exposure_layout.addWidget(self.exposure_detail)

            exposure_box.setLayout(exposure_layout)
            layout.addWidget(exposure_box)

            # Last update timestamp
            self.last_update_label = QLabel("Last updated: Never")
            self.last_update_label.setStyleSheet("color: #666; font-size: 10px;")
            layout.addWidget(self.last_update_label)

            layout.addStretch()
            self.setLayout(layout)

        def update_account_summary(
            self,
            net_liq: float,
            buying_power: float = 0.0,
            cash: float = 0.0,
            daily_pnl: float = 0.0,
            total_pnl: float = 0.0,
        ):
            """Update account summary values."""
            self._net_liq = net_liq
            self._buying_power = buying_power
            self._cash = cash
            self._daily_pnl = daily_pnl
            self._total_pnl = total_pnl

            self.netliq_label.setText(f"Net Liquidation: ${net_liq:,.2f}")
            self.buying_power_label.setText(f"Buying Power: ${buying_power:,.2f}")
            self.cash_label.setText(f"Cash: ${cash:,.2f}")

            # Color-code P&L
            daily_color = "#0a0" if daily_pnl >= 0 else "#b00"
            total_color = "#0a0" if total_pnl >= 0 else "#b00"
            daily_sign = "+" if daily_pnl >= 0 else ""
            total_sign = "+" if total_pnl >= 0 else ""

            self.daily_pnl_label.setText(f"Daily P&L: <span style='color:{daily_color}'>{daily_sign}${daily_pnl:,.2f}</span>")
            self.daily_pnl_label.setTextFormat(Qt.RichText)
            self.total_pnl_label.setText(f"Total P&L: <span style='color:{total_color}'>{total_sign}${total_pnl:,.2f}</span>")
            self.total_pnl_label.setTextFormat(Qt.RichText)

            self._update_exposure()
            self._update_timestamp()

        def update_positions(self, positions: List[Dict[str, Any]]):
            """Update positions table."""
            self._positions = positions

            self.positions_table.setRowCount(0)
            self.positions_table.setRowCount(len(positions))

            total_position_value = 0.0

            for row, pos in enumerate(positions):
                symbol = pos.get("symbol", "")
                qty = pos.get("position", 0)
                avg_cost = pos.get("avgCost", 0.0)
                current_price = pos.get("currentPrice", avg_cost)  # Fallback to avgCost
                market_value = pos.get("marketValue", qty * current_price)

                # Calculate P&L
                cost_basis = qty * avg_cost
                pnl = market_value - cost_basis if qty != 0 else 0
                pnl_pct = (pnl / cost_basis * 100) if cost_basis != 0 else 0

                total_position_value += abs(market_value)

                # Create table items
                items = [
                    QTableWidgetItem(str(symbol)),
                    QTableWidgetItem(str(qty)),
                    QTableWidgetItem(f"${avg_cost:.2f}"),
                    QTableWidgetItem(f"${current_price:.2f}"),
                    QTableWidgetItem(f"${pnl:+,.2f}"),
                    QTableWidgetItem(f"{pnl_pct:+.2f}%"),
                ]

                # Color-code P&L columns
                pnl_color = QColor("#0a0") if pnl >= 0 else QColor("#b00")
                items[4].setForeground(pnl_color)
                items[5].setForeground(pnl_color)

                for col, item in enumerate(items):
                    item.setTextAlignment(Qt.AlignCenter)
                    self.positions_table.setItem(row, col, item)

            # Update position count
            count = len(positions)
            self.position_count_label.setText(
                f"{count} open position{'s' if count != 1 else ''}"
                if count > 0 else "No open positions"
            )

            self._update_exposure()
            self._update_timestamp()

        def _update_exposure(self):
            """Update exposure bar based on positions."""
            if self._net_liq <= 0:
                self.exposure_bar.setValue(0)
                self.exposure_bar.setFormat("Invested: --%")
                self.exposure_detail.setText("Cash: -- | Invested: --")
                return

            # Calculate total invested
            invested = sum(
                abs(p.get("position", 0) * p.get("avgCost", 0))
                for p in self._positions
            )

            exposure_pct = min(100, (invested / self._net_liq) * 100)
            cash_pct = 100 - exposure_pct

            self.exposure_bar.setValue(int(exposure_pct))
            self.exposure_bar.setFormat(f"Invested: {exposure_pct:.1f}%")
            self.exposure_detail.setText(
                f"Cash: ${self._net_liq - invested:,.2f} ({cash_pct:.1f}%) | "
                f"Invested: ${invested:,.2f} ({exposure_pct:.1f}%)"
            )

        def _update_timestamp(self):
            """Update the last update timestamp."""
            now = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.setText(f"Last updated: {now}")

        def clear(self):
            """Clear all data."""
            self._net_liq = 0.0
            self._buying_power = 0.0
            self._cash = 0.0
            self._positions = []
            self._total_pnl = 0.0
            self._daily_pnl = 0.0

            self.netliq_label.setText("Net Liquidation: --")
            self.buying_power_label.setText("Buying Power: --")
            self.cash_label.setText("Cash: --")
            self.daily_pnl_label.setText("Daily P&L: --")
            self.total_pnl_label.setText("Total P&L: --")
            self.positions_table.setRowCount(0)
            self.position_count_label.setText("No open positions")
            self.exposure_bar.setValue(0)
            self.exposure_bar.setFormat("Invested: --%")
            self.exposure_detail.setText("Cash: -- | Invested: --")
            self.last_update_label.setText("Last updated: Never")
else:
    # Stub class when Qt is not available
    class PortfolioWidget:
        def __init__(self, parent=None):
            pass
