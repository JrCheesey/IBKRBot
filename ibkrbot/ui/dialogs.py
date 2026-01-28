from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QCheckBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)

from ..core.config import load_config, save_user_config, default_config_path, user_config_path
from ..core.constants import RiskDefaults
from .theme import Colors, Fonts, Styles, Spacing


def validate_time_format(time_str: str) -> bool:
    """Validate HH:MM (24-hour) format."""
    pattern = r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
    return bool(re.match(pattern, time_str.strip()))


def validate_host(host: str) -> bool:
    """Validate IP address or hostname."""
    host = host.strip()
    if not host:
        return False

    # Simple IP address check
    ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
    if re.match(ip_pattern, host):
        parts = host.split(".")
        return all(0 <= int(p) <= 255 for p in parts)

    # Hostname check (alphanumeric, hyphens, dots)
    hostname_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?)*$"
    return bool(re.match(hostname_pattern, host))


def _pct_to_float(pct: float) -> float:
    return pct / 100.0


def _float_to_pct(x: float) -> float:
    return x * 100.0


def _fmt_money(x: float) -> str:
    try:
        return f"{x:,.2f}"
    except Exception:
        return str(x)


class TradeTicketDialog(QDialog):
    def __init__(self, plan: Dict[str, Any], cfg: Dict[str, Any], *, risk_over: bool, mode: str, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.cfg = cfg
        self.risk_over = risk_over
        self.mode = mode
        self.setWindowTitle("Confirm Trade Ticket")
        self.resize(Spacing.DIALOG_WIDTH_SMALL, Spacing.DIALOG_HEIGHT_STANDARD)

        symbol = plan.get("symbol", "—")
        listing = plan.get("listing", {}) or {}
        exchange = listing.get("exchange", "SMART")
        currency = listing.get("currency", "USD")
        lv = plan.get("levels", {})
        rk = plan.get("risk", {})

        entry = float(lv.get("entry_limit", 0.0) or 0.0)
        stop = float(lv.get("stop", 0.0) or 0.0)
        take = float(lv.get("take_profit", 0.0) or 0.0)
        atr = float(lv.get("atr", 0.0) or 0.0)
        qty = int(rk.get("qty", 0) or 0)
        netliq = float(rk.get("net_liq", 0.0) or 0.0)
        est_notional = float(rk.get("estimated_notional", qty * entry) or (qty * entry))
        est_risk = float(rk.get("estimated_risk", qty * max(entry - stop, 0.0)) or (qty * max(entry - stop, 0.0)))
        take_r = float(rk.get("take_r", 0.0) or 0.0)

        max_notional_pct = float(cfg.get("risk", {}).get("max_notional_pct", RiskDefaults.MAX_NOTIONAL_PCT))
        max_loss_pct = float(cfg.get("risk", {}).get("max_loss_pct", RiskDefaults.MAX_LOSS_PCT))
        max_notional = max_notional_pct * netliq if netliq > 0 else 0.0
        max_loss = max_loss_pct * netliq if netliq > 0 else 0.0

        outer = QVBoxLayout()

        direction = plan.get("direction", "Long")
        title = QLabel(f"{symbol} — Bracket Order ({direction})")
        f = QFont()
        f.setPointSize(Fonts.SIZE_TITLE)
        f.setBold(True)
        title.setFont(f)
        outer.addWidget(title)

        sub = QLabel(f"Exchange: {exchange}   Currency: {currency}   Mode: {mode.upper()}")
        sub.setStyleSheet(Styles.hint_text())
        outer.addWidget(sub)

        # Warnings
        warnings: List[str] = []
        if mode != "paper":
            warnings.append("LIVE MODE: You are about to submit to a live account.")
        if risk_over:
            warnings.append("Risk limits exceeded: override confirmation is required.")
        if currency.upper() == "CAD":
            warnings.append("Canadian listings may be restricted for API trading depending on account settings. If rejected, IBKR will return an error.")

        if warnings:
            warn = QLabel("⚠ " + "\n⚠ ".join(warnings))
            warn.setWordWrap(True)
            warn.setStyleSheet(Styles.error_banner())
            outer.addWidget(warn)

        # Summary grid
        form = QFormLayout()
        form.addRow("Entry (LMT):", QLabel(f"{entry:.2f}"))
        form.addRow("Stop (STP):", QLabel(f"{stop:.2f}"))
        form.addRow("Take (LMT):", QLabel(f"{take:.2f}"))
        form.addRow("Qty:", QLabel(str(qty)))
        form.addRow("ATR:", QLabel(f"{atr:.4f}"))
        form.addRow("Est Notional:", QLabel(_fmt_money(est_notional)))
        form.addRow("Est Max Loss:", QLabel(_fmt_money(est_risk)))
        form.addRow("Take R:", QLabel(f"{take_r:.2f}"))

        if netliq > 0:
            form.addRow("NetLiq:", QLabel(_fmt_money(netliq)))
            form.addRow("Max Notional (cfg):", QLabel(f"{_fmt_money(max_notional)} ({max_notional_pct*100:.2f}%)"))
            form.addRow("Max Loss (cfg):", QLabel(f"{_fmt_money(max_loss)} ({max_loss_pct*100:.2f}%)"))

        box = QWidget()
        box.setLayout(form)
        outer.addWidget(box)

        self.cb_confirm = QCheckBox("I confirm I reviewed the ticket and want to submit this bracket order.")
        outer.addWidget(self.cb_confirm)

        need_phrase = (mode != "paper") or risk_over
        self.phrase_label = QLabel("Type PLACE to enable Submit:")
        self.phrase_edit = QLineEdit()
        self.phrase_edit.setPlaceholderText("PLACE")
        if not need_phrase:
            self.phrase_label.hide()
            self.phrase_edit.hide()

        outer.addWidget(self.phrase_label)
        outer.addWidget(self.phrase_edit)

        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_copy = QPushButton("Copy Ticket")
        self.btn_submit = QPushButton("Submit")
        self.btn_submit.setDefault(True)
        self.btn_submit.setEnabled(False)

        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_copy)
        btns.addWidget(self.btn_submit)
        outer.addLayout(btns)

        self.setLayout(outer)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_copy.clicked.connect(self._on_copy)
        self.btn_submit.clicked.connect(self.accept)
        self.cb_confirm.stateChanged.connect(self._update_state)
        self.phrase_edit.textChanged.connect(self._update_state)

        self._update_state()

    def _on_copy(self) -> None:
        """Copy trade ticket summary to clipboard"""
        summary = format_trade_ticket_summary(self.plan, self.cfg)
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(summary)
        QMessageBox.information(self, "Copied", "Trade ticket copied to clipboard!")

    def _update_state(self) -> None:
        if not self.cb_confirm.isChecked():
            self.btn_submit.setEnabled(False)
            return
        need_phrase = self.phrase_edit.isVisible()
        if need_phrase and self.phrase_edit.text().strip().upper() != "PLACE":
            self.btn_submit.setEnabled(False)
            return
        self.btn_submit.setEnabled(True)


class DiffDialog(QDialog):
    def __init__(self, title: str, diff_lines: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(Spacing.DIALOG_WIDTH_LARGE, Spacing.DIALOG_HEIGHT_STANDARD)
        lay = QVBoxLayout()
        lab = QLabel("Draft vs Placed differences:")
        f = lab.font()
        f.setBold(True)
        lab.setFont(f)
        lay.addWidget(lab)

        from PySide6.QtWidgets import QTextEdit
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setLineWrapMode(QTextEdit.NoWrap)
        self.editor.setText(diff_lines)
        lay.addWidget(self.editor)

        btns = QHBoxLayout()
        btns.addStretch(1)
        b = QPushButton("Close")
        b.clicked.connect(self.accept)
        btns.addWidget(b)
        lay.addLayout(btns)
        self.setLayout(lay)


def compute_plan_diff(draft: Dict[str, Any], placed: Dict[str, Any]) -> str:
    def g(d: Dict[str, Any], path: str, default: Any = None) -> Any:
        cur: Any = d
        for part in path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    fields = [
        ("created_at", "created_at"),
        ("symbol", "symbol"),
        ("exchange", "exchange"),
        ("currency", "currency"),
        ("entry_limit", "levels.entry_limit"),
        ("stop", "levels.stop"),
        ("take_profit", "levels.take_profit"),
        ("qty", "risk.qty"),
        ("atr", "levels.atr"),
        ("risk_per_share", "levels.risk_per_share"),
        ("est_notional", "risk.estimated_notional"),
        ("est_risk", "risk.estimated_risk"),
        ("take_r", "risk.take_r"),
    ]

    lines: List[str] = []
    lines.append(f"{'FIELD':<18} | {'DRAFT':>18} | {'PLACED':>18}")
    lines.append("-"*60)
    changed = 0
    for name, path in fields:
        a = g(draft, path)
        b = g(placed, path)
        if a != b:
            changed += 1
            lines.append(f"{name:<18} | {str(a):>18} | {str(b):>18}")
    if changed == 0:
        lines.append("(No differences found for key fields.)")
    return "\n".join(lines)


class SettingsDialog(QDialog):
    """
    Simple settings dialog that edits the user's config.json (merged with defaults at runtime).
    """
    def __init__(self, cfg: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(Spacing.DIALOG_WIDTH_MEDIUM, Spacing.DIALOG_HEIGHT_STANDARD)

        self._default = load_config()
        # Load raw defaults (not merged with user config) for reset
        try:
            import json
            self._resource_default = json.loads(default_config_path().read_text(encoding="utf-8"))
        except Exception:
            self._resource_default = self._default

        self.cfg = cfg

        outer = QVBoxLayout()
        self.tabs = QTabWidget()

        self.tab_ibkr = QWidget()
        self.tab_risk = QWidget()
        self.tab_strategy = QWidget()
        self.tab_data = QWidget()
        self.tab_janitor = QWidget()
        self.tab_symbols = QWidget()

        self.tabs.addTab(self.tab_ibkr, "IBKR")
        self.tabs.addTab(self.tab_risk, "Risk")
        self.tabs.addTab(self.tab_strategy, "Strategy")
        self.tabs.addTab(self.tab_data, "Data")
        self.tabs.addTab(self.tab_janitor, "Janitor")
        self.tabs.addTab(self.tab_symbols, "Symbols")
        outer.addWidget(self.tabs)

        # ---- IBKR tab ----
        f1 = QFormLayout()
        self.ed_host = QLineEdit(str(cfg.get("ibkr", {}).get("host", "127.0.0.1")))
        self.sp_paper = QSpinBox(); self.sp_paper.setRange(1, 65535); self.sp_paper.setValue(int(cfg.get("ibkr", {}).get("port_paper", 4002)))
        self.sp_live = QSpinBox(); self.sp_live.setRange(1, 65535); self.sp_live.setValue(int(cfg.get("ibkr", {}).get("port_live", 4001)))
        self.sp_client = QSpinBox(); self.sp_client.setRange(0, 999999); self.sp_client.setValue(int(cfg.get("ibkr", {}).get("client_id", 7)))
        self.cb_mode = QComboBox(); self.cb_mode.addItems(["paper","live"]); self.cb_mode.setCurrentText(str(cfg.get("ibkr", {}).get("mode","paper")))

        # Add helpful tooltips
        self.ed_host.setToolTip("IP address or hostname of IB Gateway/TWS. Usually 127.0.0.1 for local.")
        self.sp_paper.setToolTip("Paper trading port. Default: 4002 (IB Gateway) or 7497 (TWS)")
        self.sp_live.setToolTip("Live trading port. Default: 4001 (IB Gateway) or 7496 (TWS)")
        self.sp_client.setToolTip("Client ID to identify this connection. Use different IDs for multiple apps.")
        self.cb_mode.setToolTip("Paper is safest. Live will require typing 'PLACE' to confirm orders.")

        f1.addRow("Host:", self.ed_host)
        f1.addRow("Paper Port:", self.sp_paper)
        f1.addRow("Live Port:", self.sp_live)
        f1.addRow("Client ID:", self.sp_client)
        f1.addRow("Mode:", self.cb_mode)

        note = QLabel("Note: Run IB Gateway for API connectivity. You can run TWS separately for visuals.")
        note.setWordWrap(True)
        note.setStyleSheet(Styles.hint_text())
        f1.addRow(note)

        self.tab_ibkr.setLayout(f1)

        # ---- Risk tab ----
        f2 = QFormLayout()
        self.sp_max_notional = QDoubleSpinBox(); self.sp_max_notional.setDecimals(2); self.sp_max_notional.setRange(0.1, 100.0)
        self.sp_max_notional.setValue(_float_to_pct(float(cfg.get("risk", {}).get("max_notional_pct", 0.05))))
        self.sp_max_loss = QDoubleSpinBox(); self.sp_max_loss.setDecimals(3); self.sp_max_loss.setRange(0.01, 10.0)
        self.sp_max_loss.setValue(_float_to_pct(float(cfg.get("risk", {}).get("max_loss_pct", 0.005))))
        self.sp_r_mult = QDoubleSpinBox(); self.sp_r_mult.setDecimals(2); self.sp_r_mult.setRange(0.25, 10.0)
        self.sp_r_mult.setValue(float(cfg.get("risk", {}).get("r_multiple_take", 2.0)))
        self.cb_no_dupe_pos = QCheckBox("Block placing if a position exists for the same symbol")
        self.cb_no_dupe_pos.setChecked(bool(cfg.get("risk", {}).get("no_dupe_block_on_position", True)))

        # Add helpful tooltips
        self.sp_max_notional.setToolTip("Maximum position size as % of account. Recommended: 5-10%")
        self.sp_max_loss.setToolTip("Maximum loss per trade as % of account. Recommended: 0.5-1%")
        self.sp_r_mult.setToolTip("Take profit target as multiple of risk. 2R means profit = 2x risk amount")
        self.cb_no_dupe_pos.setToolTip("Prevents placing new brackets if you already have a position in the symbol")

        f2.addRow("Max notional (% of NetLiq):", self.sp_max_notional)
        f2.addRow("Max loss (% of NetLiq):", self.sp_max_loss)
        f2.addRow("Take profit (R multiple):", self.sp_r_mult)
        f2.addRow(self.cb_no_dupe_pos)

        self.tab_risk.setLayout(f2)

        # ---- Strategy tab ----
        f3 = QFormLayout()
        self.cb_interval = QComboBox()
        self.cb_interval.addItems(["1h","30m","15m","1d"])
        self.cb_interval.setCurrentText(str(cfg.get("strategy", {}).get("bar_interval","1h")))
        self.sp_lookback = QSpinBox(); self.sp_lookback.setRange(5, 365); self.sp_lookback.setValue(int(cfg.get("strategy", {}).get("lookback_days",30)))
        self.sp_atr = QSpinBox(); self.sp_atr.setRange(5, 100); self.sp_atr.setValue(int(cfg.get("strategy", {}).get("atr_period",14)))
        self.sp_pullback = QDoubleSpinBox(); self.sp_pullback.setDecimals(2); self.sp_pullback.setRange(0.0, 1.0); self.sp_pullback.setSingleStep(0.05)
        self.sp_pullback.setValue(float(cfg.get("strategy", {}).get("pullback_pct",0.25)))
        self.sp_stop_atr = QDoubleSpinBox(); self.sp_stop_atr.setDecimals(2); self.sp_stop_atr.setRange(0.1, 5.0); self.sp_stop_atr.setSingleStep(0.1)
        self.sp_stop_atr.setValue(float(cfg.get("strategy", {}).get("stop_atr_mult",1.0)))
        self.sp_limit_off = QDoubleSpinBox(); self.sp_limit_off.setDecimals(2); self.sp_limit_off.setRange(0.0, 5.0); self.sp_limit_off.setSingleStep(0.1)
        self.sp_limit_off.setValue(float(cfg.get("strategy", {}).get("limit_offset_atr",0.25)))

        # Add helpful tooltips
        self.cb_interval.setToolTip("Time interval for price bars. 1h works well for swing trading.")
        self.sp_lookback.setToolTip("How many days of historical data to fetch for analysis")
        self.sp_atr.setToolTip("Period for ATR calculation. Standard is 14 periods.")
        self.sp_pullback.setToolTip("How much below last close to set entry. 0.25 = 25% of ATR below close")
        self.sp_stop_atr.setToolTip("Stop distance as multiple of ATR. 1.0 = 1 ATR below entry")
        self.sp_limit_off.setToolTip("Additional offset for entry limit below pullback target")

        f3.addRow("Bar interval:", self.cb_interval)
        f3.addRow("Lookback days:", self.sp_lookback)
        f3.addRow("ATR period:", self.sp_atr)
        f3.addRow("Pullback pct (0-1):", self.sp_pullback)
        f3.addRow("Stop ATR multiple:", self.sp_stop_atr)
        f3.addRow("Entry limit offset (ATR):", self.sp_limit_off)

        self.tab_strategy.setLayout(f3)

        # ---- Data tab ----
        f4 = QFormLayout()
        self.sp_yf_timeout = QSpinBox(); self.sp_yf_timeout.setRange(5, 120); self.sp_yf_timeout.setValue(int(cfg.get("data", {}).get("yfinance_timeout_s", 20)))
        self.sp_yf_timeout.setToolTip("Max seconds to wait for Yahoo Finance data. Increase if you have slow internet.")
        f4.addRow("yfinance timeout (seconds):", self.sp_yf_timeout)
        self.tab_data.setLayout(f4)

        # ---- Janitor tab ----
        f5 = QFormLayout()
        self.ed_eod = QLineEdit(str(cfg.get("janitor", {}).get("eod_local","15:45")))
        self.sp_stale = QSpinBox(); self.sp_stale.setRange(1, 1440); self.sp_stale.setValue(int(cfg.get("janitor", {}).get("stale_minutes",120)))
        self.sp_mgr_poll = QSpinBox(); self.sp_mgr_poll.setRange(2, 300); self.sp_mgr_poll.setValue(int(cfg.get("manager", {}).get("poll_seconds",10)))
        self.cb_snapshot = QCheckBox("Enable live price snapshot for R-multiple calculation")
        self.cb_snapshot.setChecked(bool(cfg.get("manager", {}).get("enable_snapshot_price", False)))

        # Add helpful tooltips
        self.ed_eod.setToolTip("End-of-day time in 24-hour format (e.g., 15:45 = 3:45 PM)")
        self.sp_stale.setToolTip("How long to keep plan files before considering them stale")
        self.sp_mgr_poll.setToolTip("How often the manager checks positions and orders (seconds)")
        self.cb_snapshot.setToolTip("Enable this if you have market data subscription. Disable to prevent subscription errors.")

        f5.addRow("EOD local (HH:MM):", self.ed_eod)
        f5.addRow("Stale minutes:", self.sp_stale)
        f5.addRow("Manager poll seconds:", self.sp_mgr_poll)
        f5.addRow(self.cb_snapshot)
        self.tab_janitor.setLayout(f5)

        # ---- Symbols tab ----
        v_syms = QVBoxLayout()
        help_syms = QLabel("Edit the symbol list used in the dropdown. For Canadian ETFs, API trading may be restricted depending on IB settings.")
        help_syms.setWordWrap(True)
        help_syms.setStyleSheet(Styles.hint_text())
        v_syms.addWidget(help_syms)

        self.tbl_syms = QTableWidget(0, 3)
        self.tbl_syms.setHorizontalHeaderLabels(["Symbol", "Exchange", "Currency"])
        self.tbl_syms.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_syms.setAlternatingRowColors(True)

        symbols = cfg.get("symbols", [])
        self.tbl_syms.setRowCount(len(symbols))
        for i, s in enumerate(symbols):
            self.tbl_syms.setItem(i, 0, QTableWidgetItem(str(s.get("symbol",""))))
            self.tbl_syms.setItem(i, 1, QTableWidgetItem(str(s.get("exchange","SMART"))))
            self.tbl_syms.setItem(i, 2, QTableWidgetItem(str(s.get("currency","USD"))))

        v_syms.addWidget(self.tbl_syms)

        row_btns = QHBoxLayout()
        self.btn_add_sym = QPushButton("Add")
        self.btn_del_sym = QPushButton("Remove Selected")
        row_btns.addWidget(self.btn_add_sym)
        row_btns.addWidget(self.btn_del_sym)
        row_btns.addStretch(1)
        v_syms.addLayout(row_btns)

        self.btn_add_sym.clicked.connect(self._add_symbol_row)
        self.btn_del_sym.clicked.connect(self._del_symbol_row)

        self.tab_symbols.setLayout(v_syms)

        # ---- bottom buttons ----
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_open_cfg = QPushButton("Open config.json")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_save = QPushButton("Save")

        bottom.addWidget(self.btn_open_cfg)
        bottom.addWidget(self.btn_reset)
        bottom.addWidget(self.btn_cancel)
        bottom.addWidget(self.btn_save)
        outer.addLayout(bottom)
        self.setLayout(outer)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._save)
        self.btn_reset.clicked.connect(self._reset_defaults)
        self.btn_open_cfg.clicked.connect(self._open_config_path)

        self.saved_config: Optional[Dict[str, Any]] = None

    def _add_symbol_row(self) -> None:
        r = self.tbl_syms.rowCount()
        self.tbl_syms.insertRow(r)
        self.tbl_syms.setItem(r, 0, QTableWidgetItem("SPY"))
        self.tbl_syms.setItem(r, 1, QTableWidgetItem("SMART"))
        self.tbl_syms.setItem(r, 2, QTableWidgetItem("USD"))

    def _del_symbol_row(self) -> None:
        rows = sorted({i.row() for i in self.tbl_syms.selectedIndexes()}, reverse=True)
        for r in rows:
            self.tbl_syms.removeRow(r)

    def _open_config_path(self) -> None:
        try:
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl
            p = user_config_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            if not p.exists():
                p.write_text("{}", encoding="utf-8")
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
        except Exception as e:
            QMessageBox.warning(self, "Open failed", str(e))

    def _reset_defaults(self) -> None:
        if QMessageBox.question(self, "Reset to Defaults", "Reset settings in this dialog back to defaults? (You still need to Save.)") != QMessageBox.Yes:
            return
        d = self._resource_default

        self.ed_host.setText(str(d.get("ibkr", {}).get("host","127.0.0.1")))
        self.sp_paper.setValue(int(d.get("ibkr", {}).get("port_paper",4002)))
        self.sp_live.setValue(int(d.get("ibkr", {}).get("port_live",4001)))
        self.sp_client.setValue(int(d.get("ibkr", {}).get("client_id",7)))
        self.cb_mode.setCurrentText(str(d.get("ibkr", {}).get("mode","paper")))

        self.sp_max_notional.setValue(_float_to_pct(float(d.get("risk", {}).get("max_notional_pct",0.05))))
        self.sp_max_loss.setValue(_float_to_pct(float(d.get("risk", {}).get("max_loss_pct",0.005))))
        self.sp_r_mult.setValue(float(d.get("risk", {}).get("r_multiple_take",2.0)))
        self.cb_no_dupe_pos.setChecked(bool(d.get("risk", {}).get("no_dupe_block_on_position", True)))

        self.cb_interval.setCurrentText(str(d.get("strategy", {}).get("bar_interval","1h")))
        self.sp_lookback.setValue(int(d.get("strategy", {}).get("lookback_days",30)))
        self.sp_atr.setValue(int(d.get("strategy", {}).get("atr_period",14)))
        self.sp_pullback.setValue(float(d.get("strategy", {}).get("pullback_pct",0.25)))
        self.sp_stop_atr.setValue(float(d.get("strategy", {}).get("stop_atr_mult",1.0)))
        self.sp_limit_off.setValue(float(d.get("strategy", {}).get("limit_offset_atr",0.25)))

        self.sp_yf_timeout.setValue(int(d.get("data", {}).get("yfinance_timeout_s",20)))

        self.ed_eod.setText(str(d.get("janitor", {}).get("eod_local","15:45")))
        self.sp_stale.setValue(int(d.get("janitor", {}).get("stale_minutes",120)))
        self.sp_mgr_poll.setValue(int(d.get("manager", {}).get("poll_seconds",10)))
        self.cb_snapshot.setChecked(bool(d.get("manager", {}).get("enable_snapshot_price", False)))

        # symbols
        syms = d.get("symbols", [])
        self.tbl_syms.setRowCount(len(syms))
        for i, s in enumerate(syms):
            self.tbl_syms.setItem(i, 0, QTableWidgetItem(str(s.get("symbol",""))))
            self.tbl_syms.setItem(i, 1, QTableWidgetItem(str(s.get("exchange","SMART"))))
            self.tbl_syms.setItem(i, 2, QTableWidgetItem(str(s.get("currency","USD"))))

    def _collect_symbols(self) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        for r in range(self.tbl_syms.rowCount()):
            sym = (self.tbl_syms.item(r, 0).text().strip() if self.tbl_syms.item(r, 0) else "").upper()
            ex = (self.tbl_syms.item(r, 1).text().strip() if self.tbl_syms.item(r, 1) else "SMART").upper()
            cur = (self.tbl_syms.item(r, 2).text().strip() if self.tbl_syms.item(r, 2) else "USD").upper()
            if sym:
                out.append({"symbol": sym, "exchange": ex or "SMART", "currency": cur or "USD"})
        # De-dupe by symbol
        seen = set()
        uniq: List[Dict[str, str]] = []
        for s in out:
            if s["symbol"] in seen:
                continue
            seen.add(s["symbol"])
            uniq.append(s)
        return uniq

    def _save(self) -> None:
        """Validate inputs and save configuration."""
        # Validate host
        host = self.ed_host.text().strip()
        if not validate_host(host):
            QMessageBox.warning(
                self,
                "Invalid Host",
                "Host must be a valid IP address (e.g., 127.0.0.1) or hostname."
            )
            self.tabs.setCurrentWidget(self.tab_ibkr)
            self.ed_host.setFocus()
            return

        # Validate EOD time format
        eod_time = self.ed_eod.text().strip()
        if not validate_time_format(eod_time):
            QMessageBox.warning(
                self,
                "Invalid EOD Time",
                "EOD time must be in HH:MM format (24-hour).\nExample: 15:45"
            )
            self.tabs.setCurrentWidget(self.tab_janitor)
            self.ed_eod.setFocus()
            return

        # Validate port ranges
        paper_port = int(self.sp_paper.value())
        live_port = int(self.sp_live.value())
        if paper_port == live_port:
            QMessageBox.warning(
                self,
                "Port Conflict",
                "Paper and Live ports must be different."
            )
            self.tabs.setCurrentWidget(self.tab_ibkr)
            self.sp_paper.setFocus()
            return

        # Build a merged config dict and save as user config.
        cfg = dict(self.cfg)

        cfg["ibkr"] = {
            "host": host,
            "port_paper": paper_port,
            "port_live": live_port,
            "client_id": int(self.sp_client.value()),
            "mode": self.cb_mode.currentText().strip(),
        }
        cfg["risk"] = {
            "max_notional_pct": _pct_to_float(float(self.sp_max_notional.value())),
            "max_loss_pct": _pct_to_float(float(self.sp_max_loss.value())),
            "r_multiple_take": float(self.sp_r_mult.value()),
            "no_dupe_block_on_position": bool(self.cb_no_dupe_pos.isChecked()),
        }
        cfg["strategy"] = {
            "bar_interval": self.cb_interval.currentText().strip(),
            "lookback_days": int(self.sp_lookback.value()),
            "atr_period": int(self.sp_atr.value()),
            "pullback_pct": float(self.sp_pullback.value()),
            "stop_atr_mult": float(self.sp_stop_atr.value()),
            "limit_offset_atr": float(self.sp_limit_off.value()),
        }
        cfg["data"] = {"yfinance_timeout_s": int(self.sp_yf_timeout.value())}
        cfg["janitor"] = {"eod_local": eod_time, "stale_minutes": int(self.sp_stale.value())}
        cfg["manager"] = {
            "poll_seconds": int(self.sp_mgr_poll.value()),
            "enable_snapshot_price": bool(self.cb_snapshot.isChecked())
        }
        cfg["symbols"] = self._collect_symbols()

        # Basic validation
        if cfg["ibkr"]["mode"] not in ("paper", "live"):
            QMessageBox.warning(self, "Invalid mode", "Mode must be paper or live.")
            return
        if not cfg["symbols"]:
            QMessageBox.warning(self, "No symbols", "Add at least one symbol.")
            return

        # Validate risk settings are sensible
        if cfg["risk"]["max_notional_pct"] > 0.25:
            result = QMessageBox.warning(
                self,
                "High Notional Risk",
                f"Max notional is set to {cfg['risk']['max_notional_pct']*100:.1f}% of NetLiq.\n"
                "This is higher than recommended (5-10%).\n\nAre you sure?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if result != QMessageBox.Yes:
                return

        if cfg["risk"]["max_loss_pct"] > 0.02:
            result = QMessageBox.warning(
                self,
                "High Loss Risk",
                f"Max loss is set to {cfg['risk']['max_loss_pct']*100:.2f}% of NetLiq.\n"
                "This is higher than recommended (0.5-1%).\n\nAre you sure?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if result != QMessageBox.Yes:
                return

        save_user_config(cfg)
        self.saved_config = cfg
        self.accept()


class PerformanceAnalyticsDialog(QDialog):
    """Performance analytics dialog showing trade statistics."""

    def __init__(self, trade_journal, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Performance Analytics")
        self.resize(500, 450)

        layout = QVBoxLayout()

        # Title
        title = QLabel("Trade Performance Analytics")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Get statistics
        stats = trade_journal.get_statistics()

        # Summary section
        summary_group = QWidget()
        summary_layout = QFormLayout()

        # Trade counts
        total = stats.get('total_trades', 0)
        open_trades = stats.get('open_trades', 0)
        closed = stats.get('closed_trades', 0)
        winners = stats.get('winners', 0)
        losers = stats.get('losers', 0)

        summary_layout.addRow("Total Trades:", QLabel(str(total)))
        summary_layout.addRow("Open Trades:", QLabel(str(open_trades)))
        summary_layout.addRow("Closed Trades:", QLabel(str(closed)))
        summary_layout.addRow("Winners:", QLabel(f"{winners} ({stats.get('win_rate', 0):.1f}%)"))
        summary_layout.addRow("Losers:", QLabel(str(losers)))

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # P&L section
        pnl_group = QWidget()
        pnl_layout = QFormLayout()

        total_pnl = stats.get('total_pnl', 0)
        pnl_label = QLabel(f"${total_pnl:,.2f}")
        if total_pnl > 0:
            pnl_label.setStyleSheet("color: green; font-weight: bold;")
        elif total_pnl < 0:
            pnl_label.setStyleSheet("color: red; font-weight: bold;")

        pnl_layout.addRow("Total P&L:", pnl_label)
        pnl_layout.addRow("Avg P&L per Trade:", QLabel(f"${stats.get('avg_pnl', 0):,.2f}"))
        pnl_layout.addRow("Avg Winner:", QLabel(f"${stats.get('avg_winner', 0):,.2f}"))
        pnl_layout.addRow("Avg Loser:", QLabel(f"${stats.get('avg_loser', 0):,.2f}"))
        pnl_layout.addRow("Best Trade:", QLabel(f"${stats.get('best_trade', 0):,.2f}"))
        pnl_layout.addRow("Worst Trade:", QLabel(f"${stats.get('worst_trade', 0):,.2f}"))

        pnl_group.setLayout(pnl_layout)
        layout.addWidget(pnl_group)

        # Risk metrics section
        risk_group = QWidget()
        risk_layout = QFormLayout()

        pf = stats.get('profit_factor', 0)
        if pf == float('inf'):
            pf_text = "Infinite (no losses)"
        else:
            pf_text = f"{pf:.2f}"

        risk_layout.addRow("Profit Factor:", QLabel(pf_text))
        risk_layout.addRow("Avg R-Multiple:", QLabel(f"{stats.get('avg_r_multiple', 0):.2f}R"))

        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)

        # Export section
        export_layout = QHBoxLayout()
        btn_export_csv = QPushButton("Export to CSV")
        btn_export_excel = QPushButton("Export to Excel")
        export_layout.addWidget(btn_export_csv)
        export_layout.addWidget(btn_export_excel)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        btn_export_csv.clicked.connect(lambda: self._export(trade_journal, 'csv'))
        btn_export_excel.clicked.connect(lambda: self._export(trade_journal, 'excel'))

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _export(self, journal, format_type: str) -> None:
        from PySide6.QtWidgets import QFileDialog
        from pathlib import Path
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type == 'csv':
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Export Trades to CSV",
                f"trades_{timestamp}.csv",
                "CSV Files (*.csv)"
            )
            if filepath:
                if journal.export_to_csv(Path(filepath)):
                    QMessageBox.information(self, "Export Complete", f"Trades exported to {filepath}")
                else:
                    QMessageBox.warning(self, "Export Failed", "No trades to export or error occurred.")
        else:
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Export Trades to Excel",
                f"trades_{timestamp}.xlsx",
                "Excel Files (*.xlsx)"
            )
            if filepath:
                if journal.export_to_excel(Path(filepath)):
                    QMessageBox.information(self, "Export Complete", f"Trades exported to {filepath}")
                else:
                    QMessageBox.warning(self, "Export Failed", "No trades to export or error occurred.\nNote: openpyxl package may be required for Excel export.")


def format_trade_ticket_summary(plan: Dict[str, Any], cfg: Dict[str, Any]) -> str:
    symbol = plan.get("symbol", "—")
    mode = plan.get("mode", cfg.get("ibkr", {}).get("mode", "paper"))
    direction = plan.get("direction", "Long")
    listing = plan.get("listing", {}) or {}
    exchange = listing.get("exchange", "SMART")
    currency = listing.get("currency", "USD")

    lv = plan.get("levels", {}) or {}
    rk = plan.get("risk", {}) or {}

    entry = float(lv.get("entry_limit", 0.0) or 0.0)
    stop = float(lv.get("stop", 0.0) or 0.0)
    take = float(lv.get("take_profit", 0.0) or 0.0)
    atr = float(lv.get("atr", 0.0) or 0.0)

    qty = int(rk.get("qty", 0) or 0)
    netliq = float(rk.get("net_liq", 0.0) or 0.0)
    max_notional_pct = float(cfg.get("risk", {}).get("max_notional_pct", rk.get("max_notional_pct", 0.05)))
    max_loss_pct = float(cfg.get("risk", {}).get("max_loss_pct", rk.get("max_loss_pct", 0.005)))

    est_notional = float(rk.get("estimated_notional", qty * entry) or (qty * entry))
    rps = float(lv.get("risk_per_share", abs(entry - stop)) or abs(entry - stop))
    est_risk = float(rk.get("estimated_risk", qty * rps) or (qty * rps))
    take_r = float(rk.get("take_r", 0.0) or 0.0)

    lines = []
    lines.append(f"IBKRBot Trade Ticket ({mode.upper()}) - {direction}")
    lines.append(f"Symbol: {symbol}   Exchange: {exchange}   Currency: {currency}")
    lines.append("")
    lines.append(f"ENTRY (LMT): {entry:.2f}")
    lines.append(f"STOP  (STP): {stop:.2f}")
    lines.append(f"TAKE  (LMT): {take:.2f}")
    lines.append(f"QTY: {qty}")
    lines.append("")
    lines.append(f"ATR: {atr:.4f}   Risk/Share: {rps:.2f}   Take R: {take_r:.2f}")
    lines.append(f"Est Notional: {est_notional:,.2f}")
    lines.append(f"Est Max Loss: {est_risk:,.2f}")
    if netliq > 0:
        lines.append("")
        lines.append(f"NetLiq: {netliq:,.2f}")
        lines.append(f"Max Notional: {max_notional_pct*100:.2f}%   Max Loss: {max_loss_pct*100:.2f}%")
    ca = plan.get("created_at")
    if ca:
        lines.append("")
        lines.append(f"Created: {ca}")
    return "\n".join(lines)
