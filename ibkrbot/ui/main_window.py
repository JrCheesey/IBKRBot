from __future__ import annotations
import json
import copy
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timezone

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QTextEdit, QComboBox, QSplitter, QMessageBox,
    QTableWidget, QTableWidgetItem, QGroupBox, QSizePolicy,
    QDoubleSpinBox, QSpinBox, QProgressBar, QStatusBar, QMenuBar, QMenu, QApplication, QDialog, QLineEdit
)
from PySide6.QtCore import Qt, QThread, QSettings, QUrl, QTimer
from PySide6.QtGui import QDesktopServices, QFont, QPixmap, QAction, QKeySequence, QShortcut
import logging
from pathlib import Path

from ..core.task_runner import TaskRunner, Task
from ..core.config import load_config
from ..core.plan import save_plan, latest_plan, load_json, now_iso
from ..core.features.proposer import propose_swing_plan
from ..core.features.placer import place_bracket_from_plan, DuplicateBracketError
from ..core.features.show_orders import fetch_orders_and_positions
from ..core.features.canceller import cancel_open_brackets
from ..core.features.janitor import janitor_check_and_cancel
from ..core.features.manager import ManagerWorker
from ..core.ibkr.client import IbkrClient
from ..core.paths import ensure_subdirs, resource_path
from ..core.visual.chart import save_thumbnail_from_plan
from ..core.constants import Timeouts, OrderStatus
from .logging_handler import QtLogEmitter, QtLogHandler
from .dialogs import TradeTicketDialog, SettingsDialog, DiffDialog, compute_plan_diff, format_trade_ticket_summary
from .theme import Colors, Fonts, Styles, Spacing, ThemeMode, get_theme_manager, apply_theme

# v1.0.2 feature imports
from ..core.sound import get_sound_player, SOUND_SUCCESS, SOUND_ERROR, SOUND_ORDER_FILLED, SOUND_CONNECT, SOUND_DISCONNECT
from ..core.update_checker import check_for_updates_async, UpdateInfo
from ..core.trade_journal import get_trade_journal
from ..core.alerts import get_alert_manager, AlertCondition
from ..core.system_tray import get_tray_manager
from ..core.auto_reconnect import get_reconnect_manager, ReconnectConfig

def _ts_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class MainWindow(QMainWindow):
    def __init__(self, logger: logging.Logger):
        super().__init__()
        self.logger = logger
        self.cfg = load_config()
        self.runner = TaskRunner()
        self.ib = IbkrClient(logger=self.logger)
        self._net_liq: Optional[float] = None
        self._paths = ensure_subdirs()

        self._manager_thread: Optional[QThread] = None
        self._manager_worker: Optional[ManagerWorker] = None

        self._draft_plan: Optional[Dict[str, Any]] = None
        self._draft_baseline: Optional[Tuple[float,float,float,int]] = None  # entry, stop, take, qty

        self._has_open_bracket: Optional[bool] = None
        self._last_refresh_at: Optional[str] = None

        self._settings = QSettings("IBKRBot", "IBKRBot")

        # Connection health monitoring
        self._connection_check_timer = QTimer()
        self._connection_check_timer.timeout.connect(self._check_connection_health)
        self._connection_check_timer.setInterval(30000)  # Check every 30 seconds

        # v1.0.2 feature initialization
        self._sound_player = get_sound_player()
        self._trade_journal = get_trade_journal()
        self._alert_manager = get_alert_manager()
        self._tray_manager = get_tray_manager()
        self._reconnect_manager = get_reconnect_manager()
        self._dark_mode_enabled = False

        # Setup auto-reconnect callbacks
        self._setup_auto_reconnect()

        # Set window title with version
        from ..core.constants import AppInfo
        self._update_window_title()

        self._build_menu()

        # --- Top controls ---
        self.symbol_combo = QComboBox()
        self._reload_symbol_combo(keep_current=False)

        # Mode selector (Paper/Live)
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["paper", "live"])
        current_mode = self.cfg.get("ibkr", {}).get("mode", "paper")
        self.mode_combo.setCurrentText(current_mode)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)

        # Style the mode combo based on selection
        self._update_mode_combo_style()

        self.status_label = QLabel("Idle")
        self.netliq_label = QLabel("NetLiq: (not connected)")
        self.paper_note = QLabel("")
        self.paper_note.setStyleSheet(Styles.secondary_text())

        self.last_proposal_label = QLabel("Last proposal: —")
        self.last_proposal_label.setStyleSheet(Styles.secondary_text())
        self.open_bracket_label = QLabel("Open bracket: unknown (refresh)")
        self.open_bracket_label.setStyleSheet(Styles.secondary_text())
        self.manager_label = QLabel("Manager: stopped")
        self.manager_label.setStyleSheet(Styles.secondary_text())

        # Buttons
        self.btn_connect = QPushButton("Connect")
        self.btn_propose = QPushButton("Propose + Save Draft")
        self.btn_place = QPushButton("Place Bracket (Draft)")
        self.btn_refresh = QPushButton("Show Orders / Refresh")
        self.btn_cancel = QPushButton("Cancel Open Brackets (Symbol)")
        self.btn_cancel_all = QPushButton("Cancel ALL Open Brackets")
        self.btn_janitor = QPushButton("Run Janitor (Symbol)")
        self.btn_mgr_start = QPushButton("Start Manager")
        self.btn_mgr_stop = QPushButton("Stop Manager")
        self.btn_view_plan = QPushButton("View Plan (Draft + Placed)")
        self.btn_compare = QPushButton("Compare Draft vs Placed")
        self.btn_cancel_task = QPushButton("Cancel Current Task")
        self.btn_save_draft_edits = QPushButton("Save Draft Changes")
        self.btn_copy_ticket = QPushButton("Copy Ticket Summary")

        self.btn_mgr_stop.setEnabled(False)
        self.btn_cancel_task.setEnabled(False)
        self.btn_save_draft_edits.setEnabled(False)
        self.btn_place.setEnabled(False)

        # Set tooltips (keyboard shortcuts added in _setup_shortcuts)
        self.btn_connect.setToolTip("Connect to IB Gateway and fetch net liquidation value")
        self.btn_cancel.setToolTip("Cancel all open orders for the selected symbol")
        self.btn_cancel_all.setToolTip("Cancel ALL open orders across all symbols")
        self.btn_janitor.setToolTip("Auto-cancel orders if within 20 minutes of market close")
        self.btn_mgr_start.setToolTip("Start background manager to monitor positions and calculate R-multiples")
        self.btn_mgr_stop.setToolTip("Stop the background manager")
        self.btn_view_plan.setToolTip("View full plan details (draft and placed) in JSON format")
        self.btn_compare.setToolTip("Compare draft plan vs placed plan to see differences")
        self.btn_cancel_task.setToolTip("Cancel the currently running task")
        self.btn_copy_ticket.setToolTip("Copy trade ticket summary to clipboard")

        # --- Workflow panel (guided UX) ---
        self.workflow_box = QGroupBox("Workflow")
        wf_l = QVBoxLayout()
        self.wf_step1 = QLabel("1) Connect to IB Gateway: ❌")
        self.wf_step2 = QLabel("2) Propose draft plan: ❌")
        self.wf_step3 = QLabel("3) Review / edit draft: —")
        self.wf_step4 = QLabel("4) Place bracket: —")
        self.wf_step5 = QLabel("5) Refresh & monitor: —")
        self.wf_step6 = QLabel("6) Manager: stopped")
        self.wf_step7 = QLabel("7) Janitor: on-demand")
        for w in [self.wf_step1, self.wf_step2, self.wf_step3, self.wf_step4, self.wf_step5, self.wf_step6, self.wf_step7]:
            w.setStyleSheet(Styles.workflow_step())
            wf_l.addWidget(w)

        self.wf_next = QLabel("Next: Connect to IB Gateway")
        self.wf_next.setWordWrap(True)
        self.wf_next.setStyleSheet(Styles.workflow_next_box())
        wf_l.addWidget(self.wf_next)

        self.workflow_box.setLayout(wf_l)

        # --- Proposal preview (editable draft fields) ---
        self.preview_box = QGroupBox("Proposal Preview (Draft)")
        self.preview_form = QFormLayout()

        self.lbl_symbol = QLabel("—")
        self.lbl_symbol.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.entry_spin = QDoubleSpinBox(); self.entry_spin.setDecimals(2); self.entry_spin.setMaximum(1_000_000); self.entry_spin.setValue(0)
        self.stop_spin  = QDoubleSpinBox(); self.stop_spin.setDecimals(2);  self.stop_spin.setMaximum(1_000_000);  self.stop_spin.setValue(0)
        self.take_spin  = QDoubleSpinBox(); self.take_spin.setDecimals(2);  self.take_spin.setMaximum(1_000_000);  self.take_spin.setValue(0)
        self.qty_spin   = QSpinBox(); self.qty_spin.setMaximum(10_000_000); self.qty_spin.setValue(0)

        self.entry_spin.setToolTip("Limit entry price suggested by the strategy. You can override it before saving/placing.")
        self.stop_spin.setToolTip("Stop price. Must be below entry for a long bracket.")
        self.take_spin.setToolTip("Take profit price. Typically based on an R-multiple (e.g., 2R).")
        self.qty_spin.setToolTip("Share quantity. If you override, risk checks will warn if limits are exceeded.")

        self.lbl_atr = QLabel("—"); self.lbl_atr.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_netliq = QLabel("—"); self.lbl_netliq.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_est_notional = QLabel("—"); self.lbl_est_notional.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_est_risk = QLabel("—"); self.lbl_est_risk.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_take_r = QLabel("—"); self.lbl_take_r.setTextInteractionFlags(Qt.TextSelectableByMouse)

        # Unsaved edits indicator
        self.unsaved_label = QLabel("")
        self.unsaved_label.setStyleSheet(Styles.unsaved_warning())
        self.unsaved_label.hide()

        # Risk gauge bars
        self.pb_notional = QProgressBar()
        self.pb_notional.setRange(0, 100)
        self.pb_notional.setValue(0)
        self.pb_notional.setFormat("Notional usage: —")

        self.pb_loss = QProgressBar()

        # Mini chart thumbnail
        self.chart_label = QLabel("(chart will appear after Propose)")
        self.chart_label.setMinimumHeight(150)
        self.chart_label.setMaximumHeight(200)
        self.chart_label.setAlignment(Qt.AlignCenter)
        self.chart_label.setStyleSheet(Styles.chart_border())
        self.chart_label.setScaledContents(True)
        self.pb_loss.setRange(0, 100)
        self.pb_loss.setValue(0)
        self.pb_loss.setFormat("Loss usage: —")

        # Risk banner (override warning)
        self.risk_banner = QLabel("")
        self.risk_banner.setWordWrap(True)
        self.risk_banner.setStyleSheet(Styles.warning_banner())
        self.risk_banner.hide()
        self.chart_label.setText('(chart will appear after Propose)')
        self.chart_label.setPixmap(QPixmap())

        self.preview_form.addRow("Symbol:", self.lbl_symbol)
        self.preview_form.addRow("Entry (LMT):", self.entry_spin)
        self.preview_form.addRow("Stop (STP):", self.stop_spin)
        self.preview_form.addRow("Take Profit (LMT):", self.take_spin)
        self.preview_form.addRow("Qty:", self.qty_spin)
        self.preview_form.addRow("ATR:", self.lbl_atr)
        self.preview_form.addRow("NetLiq:", self.lbl_netliq)
        self.preview_form.addRow("Est Notional:", self.lbl_est_notional)
        self.preview_form.addRow("Est Risk ($):", self.lbl_est_risk)
        self.preview_form.addRow("Take R:", self.lbl_take_r)
        self.preview_form.addRow(self.unsaved_label)
        self.preview_form.addRow(self.pb_notional)
        self.preview_form.addRow(self.pb_loss)
        self.preview_form.addRow("Chart:", self.chart_label)
        self.preview_form.addRow(self.risk_banner)
        self.preview_form.addRow(self.btn_copy_ticket)
        self.preview_form.addRow(self.btn_save_draft_edits)

        self.preview_box.setLayout(self.preview_form)

        # --- Orders/positions tables ---
        self.orders_table = QTableWidget(0, 9)
        self.orders_table.setHorizontalHeaderLabels(["OrderId","ParentId","Symbol","Action","Type","Qty","Lmt","Aux","Status"])
        self.orders_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.orders_table.setToolTip("Open orders from IBKR. Refresh to update.")
        self.orders_table.setAlternatingRowColors(True)

        self.positions_table = QTableWidget(0, 4)
        self.positions_table.setHorizontalHeaderLabels(["Symbol","Position","AvgCost","Currency"])
        self.positions_table.setAlternatingRowColors(True)

        orders_box = QGroupBox("Orders")
        vb1 = QVBoxLayout(); vb1.addWidget(self.orders_table); orders_box.setLayout(vb1)

        pos_box = QGroupBox("Positions")
        vb2 = QVBoxLayout(); vb2.addWidget(self.positions_table); pos_box.setLayout(vb2)

        right_split = QSplitter(Qt.Vertical)
        right_split.addWidget(orders_box)
        right_split.addWidget(pos_box)
        right_split.setSizes([320, 160])

        # --- Logs ---
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QTextEdit.NoWrap)

        # --- Layout ---
        top = QWidget()
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Symbol:"))
        top_layout.addWidget(self.symbol_combo)
        top_layout.addSpacing(15)
        top_layout.addWidget(QLabel("Mode:"))
        top_layout.addWidget(self.mode_combo)
        top_layout.addSpacing(10)
        top_layout.addWidget(self.btn_connect)
        top_layout.addStretch(1)
        top_layout.addWidget(self.netliq_label)
        top_layout.addWidget(self.status_label)
        top.setLayout(top_layout)

        meta = QWidget()
        meta_l = QHBoxLayout()
        meta_l.addWidget(self.last_proposal_label)
        meta_l.addWidget(self.open_bracket_label)
        meta_l.addWidget(self.manager_label)
        meta_l.addStretch(1)
        meta.setLayout(meta_l)

        btn_row1 = QWidget()
        bl1 = QHBoxLayout()
        for b in [self.btn_propose, self.btn_place, self.btn_refresh, self.btn_cancel, self.btn_cancel_all, self.btn_janitor]:
            bl1.addWidget(b)
        btn_row1.setLayout(bl1)

        btn_row2 = QWidget()
        bl2 = QHBoxLayout()
        for b in [self.btn_mgr_start, self.btn_mgr_stop, self.btn_view_plan, self.btn_compare, self.btn_cancel_task]:
            bl2.addWidget(b)
        bl2.addStretch(1)
        btn_row2.setLayout(bl2)

        mid_split = QSplitter(Qt.Horizontal)
        left = QWidget()
        vl = QVBoxLayout()
        vl.addWidget(self.workflow_box)
        vl.addWidget(self.preview_box)
        left.setLayout(vl)
        mid_split.addWidget(left)
        mid_split.addWidget(right_split)
        mid_split.setSizes([470, 650])

        central = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(top)
        layout.addWidget(self.paper_note)
        layout.addWidget(meta)
        layout.addWidget(btn_row1)
        layout.addWidget(btn_row2)
        layout.addWidget(mid_split)
        layout.addWidget(QLabel("Logs"))
        layout.addWidget(self.log_view)
        central.setLayout(layout)
        self.setCentralWidget(central)

        # --- Status bar ---
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        self.conn_dot = QLabel("●")
        self.conn_dot.setStyleSheet(Styles.connection_dot_disconnected())
        self.conn_text = QLabel("Disconnected")
        self.task_text = QLabel("Ready")
        self.task_spinner = QProgressBar()
        self.task_spinner.setRange(0, 0)  # indeterminate
        self.task_spinner.setFixedWidth(120)
        self.task_spinner.hide()

        self.status.addWidget(self.conn_dot)
        self.status.addWidget(self.conn_text)
        self.status.addPermanentWidget(self.task_text, 1)
        self.status.addPermanentWidget(self.task_spinner)

        # --- Log to UI ---
        self.qt_emitter = QtLogEmitter()
        handler = QtLogHandler(self.qt_emitter)
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        self.logger.addHandler(handler)
        self.qt_emitter.message.connect(self.log_view.append)

        # --- Signals ---
        self.btn_connect.clicked.connect(self._on_connect)
        self.btn_propose.clicked.connect(self._on_propose)
        self.btn_place.clicked.connect(self._on_place)
        self.btn_refresh.clicked.connect(self._on_refresh)
        self.btn_cancel.clicked.connect(self._on_cancel_symbol)
        self.btn_cancel_all.clicked.connect(self._on_cancel_all)
        self.btn_janitor.clicked.connect(self._on_janitor)
        self.btn_mgr_start.clicked.connect(self._on_mgr_start)
        self.btn_mgr_stop.clicked.connect(self._on_mgr_stop)
        self.btn_view_plan.clicked.connect(self._on_view_plan)
        self.btn_compare.clicked.connect(self._on_compare_plans)
        self.btn_cancel_task.clicked.connect(self.runner.cancel_current)
        self.btn_save_draft_edits.clicked.connect(self._on_save_draft_edits)
        self.btn_copy_ticket.clicked.connect(self._on_copy_ticket)

        # Live-update preview metrics + risk banner
        self.entry_spin.valueChanged.connect(lambda _v: self._on_preview_edited())
        self.stop_spin.valueChanged.connect(lambda _v: self._on_preview_edited())
        self.take_spin.valueChanged.connect(lambda _v: self._on_preview_edited())
        self.qty_spin.valueChanged.connect(lambda _v: self._on_preview_edited())

        self.runner.busy_changed.connect(self._on_busy_changed)
        self.symbol_combo.currentTextChanged.connect(lambda _s: self._sync_preview_from_latest())

        # --- Keyboard shortcuts ---
        self._setup_shortcuts()

        # Restore UI state
        self._restore_settings()
        self._sync_preview_from_latest()
        self._update_workflow()

        # Check for first run and show welcome dialog
        QTimer.singleShot(500, self._check_first_run)

    # --------------------- Menu helpers ---------------------
    def _build_menu(self) -> None:
        bar = QMenuBar(self)
        self.setMenuBar(bar)

        m_file = QMenu("&File", self)
        bar.addMenu(m_file)

        act_open_data = QAction("Open Data Folder", self)
        act_open_plans = QAction("Open Plans Folder", self)
        act_open_logs = QAction("Open Logs Folder", self)
        act_settings = QAction("Settings…", self)
        act_exit = QAction("Exit", self)

        act_open_data.triggered.connect(lambda: self._open_folder(self._paths["root"]))
        act_open_plans.triggered.connect(lambda: self._open_folder(self._paths["plans"]))
        act_open_logs.triggered.connect(lambda: self._open_folder(self._paths["logs"]))
        act_settings.triggered.connect(self._open_settings)
        act_exit.triggered.connect(self.close)

        m_file.addAction(act_open_data)
        m_file.addAction(act_open_plans)
        m_file.addAction(act_open_logs)
        m_file.addSeparator()
        act_backup = QAction("Backup Settings...", self)
        act_restore = QAction("Restore Settings...", self)
        act_backup.triggered.connect(self._on_backup_settings)
        act_restore.triggered.connect(self._on_restore_settings)
        m_file.addAction(act_backup)
        m_file.addAction(act_restore)
        m_file.addSeparator()
        m_file.addAction(act_settings)
        m_file.addSeparator()
        m_file.addAction(act_exit)

        # View menu (v1.0.2)
        m_view = QMenu("&View", self)
        bar.addMenu(m_view)

        self.act_dark_mode = QAction("Dark Mode", self)
        self.act_dark_mode.setCheckable(True)
        self.act_dark_mode.setChecked(False)
        self.act_dark_mode.triggered.connect(self._toggle_dark_mode)
        m_view.addAction(self.act_dark_mode)

        m_view.addSeparator()

        act_trade_journal = QAction("Trade Journal...", self)
        act_trade_journal.triggered.connect(self._show_trade_journal)
        m_view.addAction(act_trade_journal)

        act_alerts = QAction("Price Alerts...", self)
        act_alerts.triggered.connect(self._show_alerts)
        m_view.addAction(act_alerts)

        m_view.addSeparator()

        self.act_sound = QAction("Sound Notifications", self)
        self.act_sound.setCheckable(True)
        self.act_sound.setChecked(self._sound_player.enabled)
        self.act_sound.triggered.connect(self._toggle_sound)
        m_view.addAction(self.act_sound)

        self.act_tray = QAction("Minimize to Tray", self)
        self.act_tray.setCheckable(True)
        self.act_tray.setChecked(self._tray_manager.minimize_to_tray_enabled if self._tray_manager.is_available else False)
        self.act_tray.setEnabled(self._tray_manager.is_available)
        self.act_tray.triggered.connect(self._toggle_minimize_to_tray)
        m_view.addAction(self.act_tray)

        m_help = QMenu("&Help", self)
        bar.addMenu(m_help)

        act_start_here = QAction("Open START_HERE", self)
        act_setup = QAction("Open SETUP_CHECKLIST", self)
        act_shortcuts = QAction("Keyboard Shortcuts", self)
        act_disclaimer = QAction("View Disclaimer", self)
        act_about = QAction("About", self)

        act_start_here.triggered.connect(lambda: self._open_doc("START_HERE.txt"))
        act_setup.triggered.connect(lambda: self._open_doc("SETUP_CHECKLIST.txt"))
        act_shortcuts.triggered.connect(self._show_keyboard_shortcuts)
        act_disclaimer.triggered.connect(self._show_disclaimer)
        act_about.triggered.connect(self._about)

        m_help.addAction(act_start_here)
        m_help.addAction(act_setup)
        m_help.addSeparator()
        m_help.addAction(act_shortcuts)
        m_help.addAction(act_disclaimer)
        m_help.addSeparator()
        act_check_updates = QAction("Check for Updates...", self)
        act_check_updates.triggered.connect(self._check_for_updates)
        m_help.addAction(act_check_updates)
        m_help.addSeparator()
        m_help.addAction(act_about)

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts for common actions"""
        # Ctrl+R: Refresh orders/positions
        shortcut_refresh = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut_refresh.activated.connect(self._on_refresh)
        self.btn_refresh.setToolTip("Refresh orders/positions (Ctrl+R)")

        # Ctrl+P: Propose plan
        shortcut_propose = QShortcut(QKeySequence("Ctrl+P"), self)
        shortcut_propose.activated.connect(self._on_propose)
        self.btn_propose.setToolTip("Propose swing plan (Ctrl+P)")

        # Ctrl+L: Place bracket (if enabled)
        shortcut_place = QShortcut(QKeySequence("Ctrl+L"), self)
        shortcut_place.activated.connect(lambda: self._on_place() if self.btn_place.isEnabled() else None)
        self.btn_place.setToolTip("Place bracket order (Ctrl+L)")

        # Ctrl+S: Save draft edits (if enabled)
        shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut_save.activated.connect(lambda: self._on_save_draft_edits() if self.btn_save_draft_edits.isEnabled() else None)
        self.btn_save_draft_edits.setToolTip("Save draft changes (Ctrl+S)")

        # Ctrl+Q: Quit application
        shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        shortcut_quit.activated.connect(self.close)

        # F1: Show keyboard shortcuts help
        shortcut_help = QShortcut(QKeySequence("F1"), self)
        shortcut_help.activated.connect(self._show_keyboard_shortcuts)

    def _check_connection_health(self) -> None:
        """Periodic check for connection health"""
        if not self.ib:
            return

        try:
            is_connected = self.ib.isConnected()
            if not is_connected and self.conn_text.text() != "Disconnected":
                # Connection lost
                self.logger.warning("Connection to IB Gateway lost")
                self.conn_dot.setStyleSheet(Styles.connection_dot_disconnected())
                self.conn_text.setText("Disconnected")
                self.status_label.setText("Connection lost")
                self._update_workflow()

                # Play disconnect sound
                self._sound_player.play(SOUND_DISCONNECT)

                # Update tray status
                if self._tray_manager.is_available:
                    self._tray_manager.set_status("Disconnected")
                    self._tray_manager.show_notification("IBKRBot", "Connection to IB Gateway lost", "warning")

                # Trigger auto-reconnect
                self._reconnect_manager.on_connection_lost()
        except Exception as e:
            self.logger.error(f"Connection health check failed: {e}")

    def _open_folder(self, path: Path) -> None:
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
        except Exception as e:
            QMessageBox.warning(self, "Open folder failed", str(e))

    def _open_doc(self, filename: str) -> None:
        try:
            p = resource_path(filename)
            if not p.exists():
                QMessageBox.warning(self, "Missing doc", f"Document not found: {filename}")
                return
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
        except Exception as e:
            QMessageBox.warning(self, "Open doc failed", str(e))

    def _about(self) -> None:
        from .. import __version__, __author__
        from ..core.constants import AppInfo

        about_text = (
            f"<h2>{AppInfo.NAME}</h2>"
            f"<p><b>Version:</b> {__version__}</p>"
            f"<p><b>Author:</b> {__author__}</p>"
            f"<hr>"
            f"<p>{AppInfo.DESCRIPTION}</p>"
            f"<p><i>Human-in-the-loop: Review all proposals before placing orders.</i></p>"
            f"<hr>"
            f"<p><b>Features:</b></p>"
            f"<ul>"
            f"<li>Paper-first mode (default: safe testing)</li>"
            f"<li>ATR-based swing trading strategy</li>"
            f"<li>Risk-managed position sizing</li>"
            f"<li>Bracket orders (entry + take + stop)</li>"
            f"<li>Background position monitoring</li>"
            f"</ul>"
            f"<hr>"
            f"<p><b>Data Storage:</b> {self._paths['root']}</p>"
            f"<p><b>License:</b> MIT License (see LICENSE file)</p>"
            f"<p><b>Repository:</b> <a href='{AppInfo.REPO_URL}'>{AppInfo.REPO_URL}</a></p>"
            f"<hr>"
            f"<p><small>Powered by PySide6, yfinance, pandas, matplotlib, and Interactive Brokers API</small></p>"
        )

        msg = QMessageBox(self)
        msg.setWindowTitle(f"About {AppInfo.NAME}")
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Information)

        # Add disclaimer button
        disclaimer_btn = msg.addButton("View Disclaimer", QMessageBox.ActionRole)
        msg.addButton(QMessageBox.Ok)

        msg.exec()

        # If user clicked disclaimer, show it
        if msg.clickedButton() == disclaimer_btn:
            self._show_disclaimer()

    def _show_disclaimer(self) -> None:
        """Show the legal disclaimer dialog."""
        from ..core.constants import AppInfo

        msg = QMessageBox(self)
        msg.setWindowTitle("Legal Disclaimer")
        msg.setIcon(QMessageBox.Warning)
        msg.setText("<h3>IMPORTANT DISCLAIMER</h3>")

        disclaimer_html = AppInfo.get_disclaimer().replace("\n\n", "<br><br>")
        msg.setInformativeText(disclaimer_html)

        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def _check_first_run(self) -> None:
        """Check if this is the first run and show welcome dialog."""
        first_run_marker = self._paths["root"] / ".first_run_complete"

        if not first_run_marker.exists():
            self._show_welcome_wizard()
            # Create marker file
            try:
                first_run_marker.write_text("1")
            except Exception:
                pass

    def _show_welcome_wizard(self) -> None:
        """Show welcome dialog for first-time users."""
        from ..core.constants import AppInfo

        msg = QMessageBox(self)
        msg.setWindowTitle(f"Welcome to {AppInfo.NAME}!")
        msg.setIcon(QMessageBox.Information)

        welcome_text = f"""<h2>Welcome to {AppInfo.NAME} {AppInfo.VERSION}!</h2>

<p>This is a <b>paper-first</b> swing trading assistant for Interactive Brokers.</p>

<h3>Quick Start:</h3>
<ol>
<li><b>Start IB Gateway</b> (or TWS) in paper trading mode</li>
<li>Click <b>Settings</b> to configure connection (default: 127.0.0.1:4002)</li>
<li>Click <b>Connect</b> to establish connection</li>
<li>Select a symbol and click <b>Propose + Save Draft</b></li>
<li>Review the proposal, then click <b>Place Bracket</b> if acceptable</li>
</ol>

<h3>Important Notes:</h3>
<ul>
<li>✅ Defaults to <b>paper mode</b> for safe testing</li>
<li>⚠️ Always review plans before placing orders</li>
<li>📊 Uses ATR-based pullback strategy for entries</li>
<li>🛡️ Position sizing respects risk limits (default: 5% notional, 0.5% loss)</li>
</ul>

<p><b>Keyboard Shortcuts:</b> Ctrl+R (Refresh), Ctrl+P (Propose), Ctrl+L (Place), Ctrl+S (Settings)</p>

<p><i>See Help menu for more documentation and keyboard shortcuts.</i></p>"""

        msg.setText(welcome_text)
        msg.setTextFormat(Qt.RichText)

        # Add disclaimer button
        disclaimer_btn = msg.addButton("View Disclaimer", QMessageBox.ActionRole)
        settings_btn = msg.addButton("Open Settings", QMessageBox.ActionRole)
        msg.addButton(QMessageBox.Ok)

        msg.exec()

        # Handle button clicks
        if msg.clickedButton() == disclaimer_btn:
            self._show_disclaimer()
        elif msg.clickedButton() == settings_btn:
            self._open_settings()

    def _show_keyboard_shortcuts(self) -> None:
        """Show keyboard shortcuts reference."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setIcon(QMessageBox.Information)

        shortcuts_text = """<h3>Keyboard Shortcuts</h3>

<table style="width:100%">
<tr><td><b>Ctrl+R</b></td><td>Refresh orders and positions</td></tr>
<tr><td><b>Ctrl+P</b></td><td>Propose new plan for current symbol</td></tr>
<tr><td><b>Ctrl+L</b></td><td>Place bracket order from draft</td></tr>
<tr><td><b>Ctrl+S</b></td><td>Open Settings dialog</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>Quit application</td></tr>
<tr><td><b>F1</b></td><td>Show this help</td></tr>
</table>

<p><i>Tip: Hover over buttons to see tooltips explaining each action.</i></p>"""

        msg.setText(shortcuts_text)
        msg.setTextFormat(Qt.RichText)
        msg.exec()

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self.cfg, parent=self)
        if dlg.exec() == QDialog.Accepted and dlg.saved_config:
            self.cfg = dlg.saved_config
            self._reload_symbol_combo(keep_current=True)
            self.logger.info("Settings saved and reloaded.")
            # Update displays and workflow
            self._update_gauges()
            self._update_risk_banner()
            self._update_workflow()
            QMessageBox.information(self, "Settings", "Settings saved. (Reconnect if you changed IBKR host/ports/clientId.)")

    def _update_window_title(self) -> None:
        """Update window title to reflect current mode"""
        from ..core.constants import AppInfo
        mode = self.cfg.get("ibkr", {}).get("mode", "paper")
        mode_display = "PAPER" if mode == "paper" else "🔴 LIVE"
        self.setWindowTitle(f"{AppInfo.get_full_name()} ({mode_display})")

    def _update_mode_combo_style(self) -> None:
        """Style the mode combo based on selection"""
        mode = self.mode_combo.currentText()
        if mode == "live":
            # Red/bold for live mode - strong warning
            self.mode_combo.setStyleSheet("""
                QComboBox {
                    background-color: #ffe6e6;
                    color: #cc0000;
                    font-weight: bold;
                    border: 2px solid #ff4444;
                    padding: 5px 8px;
                    font-size: 11pt;
                }
                QComboBox::drop-down {
                    border-left: 1px solid #ff4444;
                }
            """)
        else:
            # Subtle gray for paper mode - neutral
            self.mode_combo.setStyleSheet("""
                QComboBox {
                    background-color: #f5f5f5;
                    color: #333333;
                    font-weight: bold;
                    border: 2px solid #999999;
                    padding: 5px 8px;
                    font-size: 11pt;
                }
                QComboBox::drop-down {
                    border-left: 1px solid #999999;
                }
            """)

    def _on_mode_changed(self, new_mode: str) -> None:
        """Handle mode change with confirmation"""
        old_mode = self.cfg.get("ibkr", {}).get("mode", "paper")

        self.logger.info(f"Mode change requested: {old_mode} -> {new_mode}")

        # If changing to live, require strong confirmation
        if new_mode == "live" and old_mode != "live":
            if not self._confirm_live_mode_switch():
                # User cancelled, revert to paper
                self.logger.info("User cancelled live mode switch")
                self.mode_combo.blockSignals(True)
                self.mode_combo.setCurrentText("paper")
                self.mode_combo.blockSignals(False)
                self._update_mode_combo_style()  # Update style to reflect revert
                return

        # If same mode, no need to do anything
        if new_mode == old_mode:
            return

        # Update config
        if "ibkr" not in self.cfg:
            self.cfg["ibkr"] = {}
        self.cfg["ibkr"]["mode"] = new_mode

        # Save to user config
        from ..core.config import save_user_config
        save_user_config(self.cfg)
        self.logger.info(f"Mode changed and saved: {new_mode}")

        # Update UI
        self._update_mode_combo_style()
        self._update_window_title()

        # Update paper note label based on new mode
        if new_mode == "paper":
            self.paper_note.setText("✅ Paper Mode: Simulated trading (NetLiq often shows $1,000,000)")
            self.paper_note.setStyleSheet("color: #006600; font-weight: bold;")
        else:
            self.paper_note.setText("🔴 LIVE MODE: Real money! All orders require confirmation.")
            self.paper_note.setStyleSheet("color: #cc0000; font-weight: bold; background-color: #ffeeee; padding: 5px;")

        # If connected, need to reconnect with new mode
        if self.ib and self.ib.isConnected():
            reply = QMessageBox.question(
                self,
                "Reconnect Required",
                f"Mode changed to {new_mode.upper()}.\n\nReconnect now to use the new mode?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Disconnect and reconnect
                try:
                    self.ib.disconnect_and_stop()
                except Exception:
                    pass
                QTimer.singleShot(500, self._on_connect)
        else:
            QMessageBox.information(
                self,
                "Mode Changed",
                f"Mode changed to {new_mode.upper()}.\n\nClick Connect to use the new mode."
            )

    def _confirm_live_mode_switch(self) -> bool:
        """Show strong confirmation dialog for switching to live mode"""
        # Create custom dialog
        dlg = QDialog(self)
        dlg.setWindowTitle("⚠️ SWITCH TO LIVE MODE")
        dlg.setModal(True)
        dlg.resize(550, 450)

        layout = QVBoxLayout()

        # Warning header
        header = QLabel("<h2 style='color: #cc0000;'>⚠️ WARNING: LIVE TRADING MODE</h2>")
        header.setTextFormat(Qt.RichText)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Warning text
        warning_text = """<p><b>You are about to switch to LIVE trading mode.</b></p>

<p><b style='color: #cc0000;'>This means:</b></p>
<ul>
<li>❌ Orders will be placed on your REAL account</li>
<li>❌ Real money will be used</li>
<li>❌ You can lose real money</li>
<li>❌ All trades will execute for real</li>
</ul>

<p><b>Before proceeding:</b></p>
<ul>
<li>✓ Ensure IB Gateway is connected to live account (port 4001)</li>
<li>✓ Verify you have sufficient funds</li>
<li>✓ Test thoroughly in paper mode first</li>
<li>✓ Understand you may lose money</li>
</ul>"""

        warning_label = QLabel(warning_text)
        warning_label.setTextFormat(Qt.RichText)
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)

        # Confirmation input
        confirm_label = QLabel("<b>Type <span style='color: #cc0000;'>LIVE</span> below to confirm:</b>")
        confirm_label.setTextFormat(Qt.RichText)
        layout.addWidget(confirm_label)

        input_edit = QLineEdit()
        input_edit.setPlaceholderText("LIVE")
        layout.addWidget(input_edit)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        confirm_btn = QPushButton("I Understand - Switch to LIVE")
        confirm_btn.setEnabled(False)
        confirm_btn.setStyleSheet("background-color: #ff4444; color: white; font-weight: bold; padding: 8px;")

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(confirm_btn)
        layout.addLayout(button_layout)

        dlg.setLayout(layout)

        # Enable confirm button only when "LIVE" is typed
        def check_input():
            is_valid = input_edit.text().strip().upper() == "LIVE"
            confirm_btn.setEnabled(is_valid)
        input_edit.textChanged.connect(check_input)

        cancel_btn.clicked.connect(dlg.reject)
        confirm_btn.clicked.connect(dlg.accept)

        result = dlg.exec()

        if result == QDialog.Accepted and input_edit.text().strip().upper() == "LIVE":
            # Show one more final confirmation
            final = QMessageBox.warning(
                self,
                "Final Confirmation",
                "Are you absolutely sure you want to switch to LIVE trading?\n\n"
                "This is your last chance to cancel.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            return final == QMessageBox.Yes

        return False

    # --------------------- Window state ---------------------
    def _restore_settings(self) -> None:
        try:
            g = self._settings.value("geometry")
            if g:
                self.restoreGeometry(g)
            sym = self._settings.value("last_symbol")
            if sym:
                idx = self.symbol_combo.findText(str(sym))
                if idx >= 0:
                    self.symbol_combo.setCurrentIndex(idx)
        except Exception:
            pass

    def _save_settings(self) -> None:
        try:
            self._settings.setValue("geometry", self.saveGeometry())
            self._settings.setValue("last_symbol", self.symbol_combo.currentText().strip())
        except Exception:
            pass

    def closeEvent(self, event):
        # Check for unsaved draft edits
        if self._has_unsaved_edits():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved draft edits.\n\nDo you want to exit anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return

        self._save_settings()

        # Stop connection health monitoring
        self._connection_check_timer.stop()

        try:
            self._on_mgr_stop()
        except Exception:
            pass
        try:
            self.ib.disconnect_and_stop()
        except Exception:
            pass
        super().closeEvent(event)

    # --------------------- Symbol reload ---------------------
    def _reload_symbol_combo(self, keep_current: bool = True) -> None:
        cur = self.symbol_combo.currentText().strip() if keep_current else ""
        self.symbol_combo.blockSignals(True)
        self.symbol_combo.clear()
        for s in self.cfg.get("symbols", []):
            self.symbol_combo.addItem(s["symbol"])
        if cur:
            idx = self.symbol_combo.findText(cur)
            if idx >= 0:
                self.symbol_combo.setCurrentIndex(idx)
        self.symbol_combo.blockSignals(False)

    # --------------------- UI state + helpers ---------------------
    def _on_busy_changed(self, busy: bool) -> None:
        self.btn_cancel_task.setEnabled(busy)
        for b in [self.btn_connect, self.btn_propose, self.btn_place, self.btn_refresh, self.btn_cancel, self.btn_cancel_all, self.btn_janitor, self.btn_view_plan, self.btn_compare, self.btn_save_draft_edits]:
            b.setEnabled(not busy)
        # re-apply draft dependent constraints
        self._apply_draft_state()

        self.status_label.setText("Busy" if busy else "Idle")
        self.task_spinner.setVisible(busy)
        if not busy:
            self.task_text.setText("Ready")

        self._update_workflow()

    def _apply_draft_state(self) -> None:
        has_draft = self._draft_plan is not None
        if self.runner.busy:
            self.btn_place.setEnabled(False)
            self.btn_save_draft_edits.setEnabled(False)
            return
        self.btn_place.setEnabled(has_draft and self.ib.isConnected())
        self.btn_save_draft_edits.setEnabled(has_draft and self._has_unsaved_edits())
        self.btn_copy_ticket.setEnabled(has_draft)

    def _current_symbol_cfg(self) -> Dict[str, Any]:
        sym = self.symbol_combo.currentText().strip()
        for s in self.cfg.get("symbols", []):
            if s["symbol"] == sym:
                return s
        return {"symbol": sym, "exchange": "SMART", "currency": "USD"}

    def _sync_preview_from_latest(self) -> None:
        sym = self.symbol_combo.currentText().strip()
        p = latest_plan(sym, "draft")
        self._draft_plan = None
        self._draft_baseline = None
        self._has_open_bracket = None
        self.open_bracket_label.setText("Open bracket: unknown (refresh)")
        if p and p.exists():
            try:
                plan = load_json(p)
                self._draft_plan = plan
                self._show_plan(plan)
                self.last_proposal_label.setText(f"Last proposal: {plan.get('created_at','—')}")
            except Exception as e:
                self.logger.error(f"Failed to load draft plan for {sym}: {e}")
                self._clear_preview()
                QMessageBox.warning(self, "Draft Load Error", f"Failed to load draft plan:\n{str(e)}\n\nPropose a new plan.")
        else:
            self._clear_preview()
        self._apply_draft_state()
        self._update_workflow()

    def _clear_preview(self) -> None:
        self.lbl_symbol.setText("—")
        self.entry_spin.setValue(0)
        self.stop_spin.setValue(0)
        self.take_spin.setValue(0)
        self.qty_spin.setValue(0)
        self.lbl_atr.setText("—")
        self.lbl_netliq.setText("—")
        self.lbl_est_notional.setText("—")
        self.lbl_est_risk.setText("—")
        self.lbl_take_r.setText("—")
        self.pb_notional.setValue(0); self.pb_notional.setFormat("Notional usage: —")
        self.pb_loss.setValue(0); self.pb_loss.setFormat("Loss usage: —")
        self.unsaved_label.hide()
        self.risk_banner.hide()
        self.chart_label.setText('(chart will appear after Propose)')
        self.chart_label.setPixmap(QPixmap())

    def _risk_limits(self) -> Tuple[float, float, float, float, float]:
        net_liq = 0.0
        if self._draft_plan:
            try:
                net_liq = float(self._draft_plan.get("risk", {}).get("net_liq", 0.0) or 0.0)
            except Exception:
                net_liq = 0.0
        if net_liq <= 0 and self._net_liq:
            net_liq = float(self._net_liq)

        max_notional_pct = float(self.cfg.get("risk", {}).get("max_notional_pct", 0.05))
        max_loss_pct = float(self.cfg.get("risk", {}).get("max_loss_pct", 0.005))
        max_notional = max_notional_pct * net_liq
        max_loss = max_loss_pct * net_liq
        return net_liq, max_notional_pct, max_loss_pct, max_notional, max_loss

    def _compute_preview(self) -> Dict[str, float]:
        entry = float(self.entry_spin.value())
        stop = float(self.stop_spin.value())
        take = float(self.take_spin.value())
        qty = int(self.qty_spin.value())
        rps = max(entry - stop, 1e-6)
        est_notional = qty * entry
        est_risk = qty * max(entry - stop, 0.0)
        take_r = (take - entry) / rps if rps > 0 else 0.0
        return {"entry": entry, "stop": stop, "take": take, "qty": qty, "rps": rps, "est_notional": est_notional, "est_risk": est_risk, "take_r": take_r}

    def _update_gauges(self) -> None:
        if not self._draft_plan:
            self.pb_notional.setValue(0); self.pb_notional.setFormat("Notional usage: —")
            self.pb_loss.setValue(0); self.pb_loss.setFormat("Loss usage: —")
            return

        pv = self._compute_preview()
        net_liq, max_notional_pct, max_loss_pct, max_notional, max_loss = self._risk_limits()
        if net_liq <= 0 or max_notional <= 0 or max_loss <= 0:
            self.pb_notional.setValue(0); self.pb_notional.setFormat("Notional usage: —")
            self.pb_loss.setValue(0); self.pb_loss.setFormat("Loss usage: —")
            return

        notional_pct = (pv["est_notional"] / max_notional) * 100.0
        loss_pct = (pv["est_risk"] / max_loss) * 100.0

        self.pb_notional.setValue(int(min(max(notional_pct, 0.0), 100.0)))
        self.pb_loss.setValue(int(min(max(loss_pct, 0.0), 100.0)))

        self.pb_notional.setFormat(f"Notional usage: {notional_pct:.1f}% (max {max_notional_pct*100:.2f}% NetLiq)")
        self.pb_loss.setFormat(f"Loss usage: {loss_pct:.1f}% (max {max_loss_pct*100:.2f}% NetLiq)")

        if notional_pct > 100.0:
            self.pb_notional.setToolTip("Over limit. Override confirmation required.")
        else:
            self.pb_notional.setToolTip("")
        if loss_pct > 100.0:
            self.pb_loss.setToolTip("Over limit. Override confirmation required.")
        else:
            self.pb_loss.setToolTip("")
    def _update_risk_banner(self) -> bool:
        if not self._draft_plan:
            self.risk_banner.hide()
            return False

        pv = self._compute_preview()
        net_liq, max_notional_pct, max_loss_pct, max_notional, max_loss = self._risk_limits()

        # If net_liq unknown, don't warn
        if net_liq <= 0:
            self.risk_banner.hide()
            return False

        over_notional = pv["est_notional"] > max_notional + 1e-6
        over_loss = pv["est_risk"] > max_loss + 1e-6
        over = over_notional or over_loss

        if not over:
            self.risk_banner.hide()
            return False

        parts = ["⚠ Risk limits exceeded (override allowed):"]
        if over_notional:
            parts.append(f"- Notional {pv['est_notional']:,.2f} > max {max_notional:,.2f} ({max_notional_pct*100:.2f}% of NetLiq)")
        if over_loss:
            parts.append(f"- Max loss {pv['est_risk']:,.2f} > max {max_loss:,.2f} ({max_loss_pct*100:.2f}% of NetLiq)")
        parts.append("You can still save/place, but it will require an extra confirmation.")
        self.risk_banner.setText("\n".join(parts))
        self.risk_banner.show()
        return True

    def _recalc_preview_metrics(self) -> None:
        pv = self._compute_preview()
        self.lbl_est_notional.setText(f"{pv['est_notional']:,.2f}")
        self.lbl_est_risk.setText(f"{pv['est_risk']:,.2f}")
        self.lbl_take_r.setText(f"{pv['take_r']:.2f}")

    def _has_unsaved_edits(self) -> bool:
        if not self._draft_baseline:
            return False
        pv = self._compute_preview()
        e0, s0, t0, q0 = self._draft_baseline
        return (abs(pv["entry"] - e0) > 0.005) or (abs(pv["stop"] - s0) > 0.005) or (abs(pv["take"] - t0) > 0.005) or (int(pv["qty"]) != int(q0))

    def _update_unsaved_indicator(self) -> None:
        if self._has_unsaved_edits():
            self.unsaved_label.setText("Unsaved edits: values differ from last saved draft.")
            self.unsaved_label.show()
        else:
            self.unsaved_label.hide()
        self._apply_draft_state()

    def _on_preview_edited(self) -> None:
        self._recalc_preview_metrics()
        self._update_gauges()
        self._update_risk_banner()
        self._update_unsaved_indicator()
        self._update_workflow()

    def _show_plan(self, plan: Dict[str, Any]) -> None:
        self.lbl_symbol.setText(plan.get("symbol","—"))
        entry = float(plan["levels"].get("entry_limit", 0.0) or 0.0)
        stop = float(plan["levels"].get("stop", 0.0) or 0.0)
        take = float(plan["levels"].get("take_profit", 0.0) or 0.0)
        qty = int(plan["risk"].get("qty", 0) or 0)
        self._draft_baseline = (entry, stop, take, qty)

        self.entry_spin.setValue(entry)
        self.stop_spin.setValue(stop)
        self.take_spin.setValue(take)
        self.qty_spin.setValue(qty)

        self.lbl_atr.setText(f"{float(plan['levels'].get('atr',0.0) or 0.0):.4f}")
        self.lbl_netliq.setText(f"{float(plan['risk'].get('net_liq',0.0) or 0.0):,.2f}")
        self._on_preview_edited()

    def _confirm(self, title: str, text: str) -> bool:
        return QMessageBox.question(self, title, text, QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes

    def _require_connected(self) -> bool:
        if not self.ib.isConnected():
            QMessageBox.warning(self, "Not connected", "Click Connect first (IB Gateway must be running).")
            return False
        return True

    def _wire_task_logs(self, task: Task) -> None:
        task.signals.started.connect(lambda name: self.task_text.setText(f"{name}…"))
        task.signals.progress.connect(lambda m: self.task_text.setText(m))
        task.signals.progress.connect(lambda m: self.logger.info("[TASK] %s", m))
        task.signals.log.connect(lambda m: self.logger.info("[TASK] %s", m))
        task.signals.finished.connect(lambda _r: self.task_text.setText("Ready"))
        task.signals.cancelled.connect(lambda: self.task_text.setText("Cancelled"))
        task.signals.error.connect(lambda _e: self.task_text.setText("Error"))

    # --------------------- Workflow logic ---------------------
    def _update_workflow(self) -> None:
        sym = self.symbol_combo.currentText().strip()
        connected = self.ib.isConnected()
        has_draft = self._draft_plan is not None
        unsaved = self._has_unsaved_edits()
        placed_p = latest_plan(sym, "placed")
        has_placed = bool(placed_p and placed_p.exists())
        open_br = self._has_open_bracket

        self.wf_step1.setText(f"1) Connect to IB Gateway: {'✅' if connected else '❌'}")
        self.wf_step2.setText(f"2) Propose draft plan: {'✅' if has_draft else '❌'}")
        self.wf_step3.setText("3) Review / edit draft: " + ("⚠ unsaved edits" if unsaved else ("✅ reviewed" if has_draft else "—")))
        self.wf_step4.setText("4) Place bracket: " + ("✅ placed plan exists" if has_placed else ("—" if not has_draft else "pending")))
        if self._last_refresh_at:
            self.wf_step5.setText(f"5) Refresh & monitor: last refresh {self._last_refresh_at}")
        else:
            self.wf_step5.setText("5) Refresh & monitor: —")
        mgr_running = self._manager_thread is not None
        self.wf_step6.setText(f"6) Manager: {'running' if mgr_running else 'stopped'}")
        self.wf_step7.setText("7) Janitor: on-demand")

        # Next suggestion
        if self.runner.busy:
            self.wf_next.setText("Next: wait for the current task to finish (or Cancel Current Task).")
            return
        if not connected:
            self.wf_next.setText("Next: Click Connect (IB Gateway must be running on the configured host/port).")
            return
        if not has_draft:
            self.wf_next.setText("Next: Click Propose to generate a draft plan, then review the ticket.")
            return
        if unsaved:
            self.wf_next.setText("Next: Save Draft Changes (optional) to make your edits official, then Place.")
            return
        if open_br is None:
            self.wf_next.setText("Next: Click Show Orders / Refresh to confirm whether an open bracket already exists (no-duplicates safety).")
            return
        if open_br:
            self.wf_next.setText("Next: Monitor the open bracket (Refresh), start Manager if desired, or Cancel Open Brackets.")
            return
        if not has_placed:
            self.wf_next.setText("Next: Click Place Bracket. You'll see a trade ticket confirmation before submit.")
            return
        self.wf_next.setText("Next: Refresh & monitor. Start Manager to track R-multiples and manage exits if configured.")

    # --------------------- Actions ---------------------
    def _on_connect(self) -> None:
        mode = self.cfg["ibkr"]["mode"]
        port = int(self.cfg["ibkr"]["port_paper"] if mode == "paper" else self.cfg["ibkr"]["port_live"])
        host = self.cfg["ibkr"]["host"]
        client_id = int(self.cfg["ibkr"]["client_id"])

        def work(ctx):
            ctx.progress("Connecting to IBKR…")
            self.ib.connect_and_start(host, port, client_id, timeout=Timeouts.IBKR_STANDARD)
            ctx.progress("Fetching NetLiq…")
            net_liq = self.ib.get_net_liq(timeout=Timeouts.IBKR_STANDARD)
            return {"net_liq": net_liq}

        task = Task("Connect", work)
        self._wire_task_logs(task)
        task.signals.finished.connect(self._connect_done)
        task.signals.error.connect(lambda e: QMessageBox.warning(self, "Connect failed", e))
        self.runner.start(task)

    def _connect_done(self, res: Dict[str, Any]) -> None:
        self._net_liq = float(res["net_liq"])
        mode = self.cfg["ibkr"]["mode"]
        mode_display = mode.upper()
        self.netliq_label.setText(f"NetLiq: {self._net_liq:,.2f} ({mode_display})")

        # Play connect sound
        self._sound_player.play(SOUND_CONNECT)

        # Update tray status
        if self._tray_manager.is_available:
            self._tray_manager.set_status(f"Connected ({mode_display})")

        # Notify reconnect manager of successful connection
        self._reconnect_manager.on_connection_success()

        if mode == "paper":
            self.paper_note.setText("✅ Paper Mode: Simulated trading (NetLiq often shows $1,000,000)")
            self.paper_note.setStyleSheet("color: #006600; font-weight: bold;")
        else:
            self.paper_note.setText("🔴 LIVE MODE: Real money! All orders require confirmation.")
            self.paper_note.setStyleSheet("color: #cc0000; font-weight: bold; background-color: #ffeeee; padding: 5px;")

        self.logger.info("Connected. NetLiq=%.2f mode=%s", self._net_liq, mode)
        self.conn_dot.setStyleSheet(Styles.connection_dot_connected())
        self.conn_text.setText(f"Connected ({mode_display})")

        # Start connection health monitoring
        self._connection_check_timer.start()

        self._apply_draft_state()
        self._update_gauges()
        self._update_risk_banner()
        self._update_workflow()

    def _on_propose(self) -> None:
        if not self._require_connected():
            return
        symbol_cfg = self._current_symbol_cfg()

        def work(ctx):
            net_liq = self.ib.get_net_liq(timeout=Timeouts.IBKR_STANDARD)
            plan = propose_swing_plan(ctx, symbol_cfg, self.cfg, net_liq)
            path = save_plan(plan, "draft")
            return {"plan": plan, "draft_path": str(path)}

        task = Task("Propose", work)
        self._wire_task_logs(task)
        def _done(r):
            self._draft_plan = r["plan"]
            self._show_plan(r["plan"])
            self.last_proposal_label.setText(f"Last proposal: {r['plan'].get('created_at','—')}")
            self.logger.info("Draft saved: %s", r["draft_path"])
            self._update_workflow()
        task.signals.finished.connect(_done)
        task.signals.error.connect(lambda e: QMessageBox.warning(self, "Propose failed", e))
        self.runner.start(task)

    def _require_override_confirm_if_over(self, action_name: str) -> bool:
        over = self._update_risk_banner()
        if not over:
            return True
        return self._confirm(
            "Override risk limits?",
            f"{action_name} would exceed configured risk limits.\n\nProceed anyway?"
        )

    def _on_save_draft_edits(self) -> None:
        sym = self.symbol_combo.currentText().strip()
        draft_p = latest_plan(sym, "draft")
        if not draft_p:
            QMessageBox.warning(self, "No draft", "No draft plan found. Click Propose first.")
            return
        if not self._has_unsaved_edits():
            QMessageBox.information(self, "No changes", "Nothing changed from the last saved draft.")
            return

        if not self._confirm("Save Draft Changes", "Save your edited entry/stop/take/qty as a NEW draft revision?"):
            return

        if not self._require_override_confirm_if_over("Saving this draft"):
            return

        plan = load_json(draft_p)
        self._draft_plan = plan

        pv = self._compute_preview()
        entry = pv["entry"]; stop = pv["stop"]; take = pv["take"]; qty = pv["qty"]

        if qty <= 0 or entry <= 0 or stop <= 0 or take <= 0:
            QMessageBox.warning(self, "Invalid values", "Entry/Stop/Take must be > 0 and Qty must be > 0.")
            return
        if stop >= entry:
            QMessageBox.warning(self, "Invalid stop", "Stop must be below entry for a long bracket.")
            return

        plan["levels"]["entry_limit"] = round(entry, 2)
        plan["levels"]["stop"] = round(stop, 2)
        plan["levels"]["take_profit"] = round(take, 2)
        plan["levels"]["risk_per_share"] = max(entry - stop, 1e-6)
        plan["risk"]["qty"] = int(qty)
        plan["risk"]["estimated_notional"] = float(qty) * entry
        plan["risk"]["estimated_risk"] = float(qty) * max(entry - stop, 0.0)
        plan["risk"]["take_r"] = pv["take_r"]
        plan["status"]["draft"] = True
        plan["status"]["placed"] = False
        plan.setdefault("edits", []).append({"edited_at": now_iso(), "fields": ["entry_limit","stop","take_profit","qty"]})

        # Regenerate thumbnail to reflect edited levels (uses saved snapshot)
        fname = f"{plan.get('symbol','SYMBOL')}_draft.png"
        out_path = self._paths["thumbs"] / fname
        try:
            made = save_thumbnail_from_plan(plan, out_path=out_path)
            if made:
                plan.setdefault("artifacts", {})["thumbnail_rel"] = f"thumbs/{fname}"
        except Exception:
            pass

        new_p = save_plan(plan, "draft")
        self._draft_plan = plan
        self._show_plan(plan)
        QMessageBox.information(self, "Draft Saved", f"Saved new draft revision:\n{new_p}")
        self._update_workflow()

    def _on_copy_ticket(self) -> None:
        """Copy a human-readable trade ticket summary to the clipboard."""
        if not self._draft_plan:
            QMessageBox.information(self, "No draft loaded", "Load or propose a trade first, then try again.")
            return

        # Build a temporary ticket from current UI values (does not save to disk).
        plan = copy.deepcopy(self._draft_plan)
        try:
            pv = self._compute_preview()
        except Exception:
            pv = None

        if pv:
            entry, stop, take, qty, _ = pv
            plan.setdefault("levels", {})
            plan["levels"]["entry_limit"] = entry
            plan["levels"]["stop"] = stop
            plan["levels"]["take_profit"] = take
            plan.setdefault("risk", {})
            plan["risk"]["qty"] = int(qty)

        sym = self.symbol_combo.currentText().strip()
        if sym and not plan.get("symbol"):
            plan["symbol"] = sym

        try:
            ticket = format_trade_ticket_summary(plan, self.cfg)
        except Exception as e:
            QMessageBox.warning(self, "Ticket formatting error", f"Couldn't format ticket summary: {e}")
            return

        QApplication.clipboard().setText(ticket)
        self.statusBar().showMessage("Copied ticket summary to clipboard", 5000)

    def _on_place(self) -> None:
        if not self._require_connected():
            return

        # Check market hours
        from ..core.constants import MarketHours
        is_open, message = MarketHours.is_market_open()
        if not is_open:
            reply = QMessageBox.question(
                self,
                "Market Closed",
                f"{message}\n\nLimit orders can be placed anytime, but will only fill during market hours.\n\nContinue placing order?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        sym = self.symbol_combo.currentText().strip()
        draft = latest_plan(sym, "draft")
        if not draft:
            QMessageBox.warning(self, "No draft", "Propose first to create a draft plan.")
            return

        try:
            plan = load_json(draft)
        except Exception as e:
            self.logger.error(f"Failed to load draft plan: {e}")
            QMessageBox.critical(self, "Draft Load Error", f"Cannot load draft plan:\n{str(e)}\n\nPropose a new plan.")
            return

        self._draft_plan = plan

        if self._has_unsaved_edits():
            if not self._confirm("Unsaved edits", "You have unsaved draft edits. Place will use the saved draft file, not the unsaved values.\n\nContinue anyway?"):
                return

        # Build a polished trade ticket dialog for confirmation
        try:
            mode = self.cfg["ibkr"]["mode"]
            risk_over = self._update_risk_banner()
            dlg = TradeTicketDialog(plan, self.cfg, risk_over=risk_over, mode=mode, parent=self)
            if dlg.exec() != QDialog.Accepted:
                return
        except Exception as e:
            self.logger.error(f"Failed to show trade ticket dialog: {e}")
            QMessageBox.critical(self, "Dialog Error", f"Failed to show confirmation dialog:\n{str(e)}")
            return

        symbol_cfg = self._current_symbol_cfg()
        block_pos = bool(self.cfg.get("risk", {}).get("no_dupe_block_on_position", True))

        def work(ctx):
            try:
                plan2 = place_bracket_from_plan(ctx, self.ib, symbol_cfg, plan, no_dupe_block_on_position=block_pos)
            except DuplicateBracketError as e:
                raise RuntimeError(str(e))
            placed_path = save_plan(plan2, "placed")
            return {"plan": plan2, "placed_path": str(placed_path)}

        task = Task("Place Bracket", work)
        self._wire_task_logs(task)
        def _done(r):
            QMessageBox.information(self, "Placed", f"Placed plan saved:\n{r['placed_path']}\n\nRefreshing orders next…")
            self.open_bracket_label.setText("Open bracket: likely YES (refresh to confirm)")
            self._has_open_bracket = None
            self._update_workflow()

            # Play order placed sound
            self._sound_player.play(SOUND_ORDER_FILLED)

            # Log to trade journal
            placed_plan = r.get("plan", {})
            try:
                self._trade_journal.add_trade(
                    symbol=placed_plan.get("symbol", ""),
                    side=placed_plan.get("side", "long"),
                    entry_price=placed_plan.get("levels", {}).get("entry_limit", 0),
                    quantity=placed_plan.get("risk", {}).get("qty", 0),
                    stop_price=placed_plan.get("levels", {}).get("stop"),
                    take_profit_price=placed_plan.get("levels", {}).get("take_profit"),
                    strategy=placed_plan.get("strategy", "swing_pullback_atr"),
                    plan_file=r.get("placed_path"),
                )
            except Exception as e:
                self.logger.warning(f"Failed to log trade to journal: {e}")

            self._on_refresh()  # auto refresh after place
        task.signals.finished.connect(_done)
        task.signals.error.connect(lambda e: (self._sound_player.play(SOUND_ERROR), QMessageBox.warning(self, "Place failed", e)))
        self.runner.start(task)

    def _on_refresh(self) -> None:
        if not self._require_connected():
            return

        def work(ctx):
            return fetch_orders_and_positions(ctx, self.ib)

        task = Task("Refresh", work)
        self._wire_task_logs(task)
        task.signals.finished.connect(self._refresh_done)
        task.signals.error.connect(lambda e: QMessageBox.warning(self, "Refresh failed", e))
        self.runner.start(task)

    def _refresh_done(self, res: Dict[str, Any]) -> None:
        """Update the Open Orders & Positions tables from a refresh result.

        IMPORTANT: this method must be import-safe (no top-level code).
        """
        orders = list(res.get("orders", []) or [])
        positions = list(res.get("positions", []) or [])

        # ---- Orders table ----
        # Bracket-friendly grouping: parent (parentId==0) followed by children (parentId==parent.orderId)
        from collections import defaultdict

        parents: dict[int, Any] = {}
        children_by_parent: dict[int, list[Any]] = defaultdict(list)
        top_level: list[Any] = []

        for o in orders:
            try:
                pid = int(getattr(o, "parentId", 0) or 0)
            except Exception:
                pid = 0
            try:
                oid = int(getattr(o, "orderId", 0) or 0)
            except Exception:
                oid = 0

            if pid:
                children_by_parent[pid].append(o)
            else:
                parents[oid] = o
                top_level.append(o)

        # Build display list with indentation levels
        display: list[tuple[Any, int]] = []
        for parent in top_level:
            try:
                poid = int(getattr(parent, "orderId", 0) or 0)
            except Exception:
                poid = 0
            display.append((parent, 0))
            for child in children_by_parent.get(poid, []):
                display.append((child, 1))

        # Orphan children (if any) — show at the end
        for pid, kids in children_by_parent.items():
            if pid not in parents:
                for child in kids:
                    display.append((child, 1))

        self.orders_table.setRowCount(0)
        self.orders_table.setRowCount(len(display))

        # Determine if there is an active bracket
        final_statuses = {"Filled", "Cancelled", "Inactive"}
        open_bracket = False
        for parent in top_level:
            try:
                poid = int(getattr(parent, "orderId", 0) or 0)
            except Exception:
                poid = 0
            kids = children_by_parent.get(poid, [])
            if not kids:
                continue
            # If any order in the bracket is still working, consider it open
            for o in [parent, *kids]:
                st = str(getattr(o, "status", "") or "")
                if st not in final_statuses:
                    open_bracket = True
                    break
            if open_bracket:
                break

        for r, (o, indent) in enumerate(display):
            sym = str(getattr(o, "symbol", "") or "")
            if indent:
                sym = "↳ " + sym

            action = str(getattr(o, "action", "") or "")
            qty = getattr(o, "totalQty", "")
            otype = str(getattr(o, "orderType", "") or "")
            lmt = getattr(o, "lmtPrice", "")
            aux = getattr(o, "auxPrice", "")
            tif = str(getattr(o, "tif", "") or "")
            status = str(getattr(o, "status", "") or "")
            oid = getattr(o, "orderId", "")

            values = [sym, action, qty, otype, lmt, aux, tif, status, oid]
            for c, v in enumerate(values):
                item = QTableWidgetItem(str(v))
                self.orders_table.setItem(r, c, item)

        self.open_bracket_label.setText("Open bracket: YES" if open_bracket else "Open bracket: NO")

        # ---- Positions table ----
        self.positions_table.setRowCount(0)
        self.positions_table.setRowCount(len(positions))
        for r, pos in enumerate(positions):
            # positions may be dicts (from ibapi) or dataclass-like
            if isinstance(pos, dict):
                sym = pos.get("symbol", "")
                qty = pos.get("position", "")
                avg = pos.get("avgCost", "")
                acct = pos.get("account", "")
            else:
                sym = getattr(pos, "symbol", "")
                qty = getattr(pos, "position", "")
                avg = getattr(pos, "avgCost", "")
                acct = getattr(pos, "account", "")

            values = [sym, qty, avg, acct]
            for c, v in enumerate(values):
                item = QTableWidgetItem(str(v))
                self.positions_table.setItem(r, c, item)

        self._last_refresh_at = datetime.now(timezone.utc)
        self._log(f"Refreshed: {len(orders)} open orders, {len(positions)} positions")
        self._update_workflow()

    def _on_cancel_symbol(self) -> None:
        if not self._require_connected():
            return
        sym = self.symbol_combo.currentText().strip()
        if not self._confirm("Confirm Cancel", f"Cancel all open orders for {sym}?"):
            return

        def work(ctx):
            return cancel_open_brackets(ctx, self.ib, sym)

        task = Task("Cancel Symbol", work)
        self._wire_task_logs(task)
        def _done(r):
            QMessageBox.information(self, "Cancel", f"Attempted: {r['attempted']}\nCancel requests sent: {r['cancelled']}\n\nRefreshing orders next…")
            self._has_open_bracket = None
            self._update_workflow()
            self._on_refresh()
        task.signals.finished.connect(_done)
        task.signals.error.connect(lambda e: QMessageBox.warning(self, "Cancel failed", e))
        self.runner.start(task)

    def _on_cancel_all(self) -> None:
        if not self._require_connected():
            return
        if not self._confirm("Confirm Cancel All", "Cancel ALL open orders (all symbols)?"):
            return

        def work(ctx):
            ctx.progress("Refreshing open orders…")
            orders = self.ib.fetch_open_orders(timeout=Timeouts.IBKR_STANDARD)
            active = [o for o in orders if o.status not in OrderStatus.FINAL_STATES]
            ctx.progress(f"Sending cancels for {len(active)} orders…")
            for o in active:
                ctx.check_cancelled()
                self.ib.cancel_order_safe(o.orderId)
            return {"active": len(active)}

        task = Task("Cancel All", work)
        self._wire_task_logs(task)
        task.signals.finished.connect(lambda r: (QMessageBox.information(self, "Cancel All", f"Cancel requests sent for {r['active']} active orders. Refreshing next…"), self._on_refresh()))
        task.signals.error.connect(lambda e: QMessageBox.warning(self, "Cancel all failed", e))
        self.runner.start(task)

    def _on_janitor(self) -> None:
        if not self._require_connected():
            return
        sym = self.symbol_combo.currentText().strip()
        if not self._confirm("Run Janitor", f"Run janitor checks for {sym}?"):
            return

        eod = self.cfg["janitor"]["eod_local"]
        stale = int(self.cfg["janitor"]["stale_minutes"])

        def work(ctx):
            return janitor_check_and_cancel(ctx, self.ib, sym, eod_local=eod, stale_minutes=stale)

        task = Task("Janitor", work)
        self._wire_task_logs(task)
        task.signals.finished.connect(lambda r: QMessageBox.information(self, "Janitor", json.dumps(r, indent=2)))
        task.signals.error.connect(lambda e: QMessageBox.warning(self, "Janitor failed", e))
        self.runner.start(task)

    def _on_mgr_start(self) -> None:
        if not self._require_connected():
            return
        if self._manager_thread is not None:
            QMessageBox.warning(self, "Manager running", "Manager is already running.")
            return

        symbol_cfg = self._current_symbol_cfg()

        self._manager_thread = QThread()
        self._manager_worker = ManagerWorker(self.ib, self.cfg, symbol_cfg)
        self._manager_worker.moveToThread(self._manager_thread)

        self._manager_thread.started.connect(self._manager_worker.run)
        self._manager_worker.log.connect(lambda m: self.logger.info("[MANAGER] %s", m))
        self._manager_worker.stopped.connect(self._mgr_stopped)

        self._manager_thread.start()
        self.btn_mgr_start.setEnabled(False)
        self.btn_mgr_stop.setEnabled(True)
        self.manager_label.setText("Manager: running")
        self.logger.info("Manager started.")
        self._update_workflow()

    def _on_mgr_stop(self) -> None:
        if self._manager_worker is None:
            return
        self._manager_worker.stop()

    def _mgr_stopped(self) -> None:
        if self._manager_thread:
            self._manager_thread.quit()
            self._manager_thread.wait(2000)
        self._manager_thread = None
        self._manager_worker = None
        self.btn_mgr_start.setEnabled(True)
        self.btn_mgr_stop.setEnabled(False)
        self.manager_label.setText("Manager: stopped")
        self.logger.info("Manager cleaned up.")
        self._update_workflow()

    def _on_view_plan(self) -> None:
        sym = self.symbol_combo.currentText().strip()
        draft_p = latest_plan(sym, "draft")
        placed_p = latest_plan(sym, "placed")

        out = []
        out.append(f"SYMBOL: {sym}")
        out.append("")
        if draft_p and draft_p.exists():
            try:
                out.append(f"DRAFT FILE: {draft_p}")
                out.append(json.dumps(load_json(draft_p), indent=2))
            except Exception as e:
                out.append(f"DRAFT FILE: {draft_p} (failed to load: {e})")
        else:
            out.append("DRAFT: (none)")
        out.append("")
        if placed_p and placed_p.exists():
            try:
                out.append(f"PLACED FILE: {placed_p}")
                out.append(json.dumps(load_json(placed_p), indent=2))
            except Exception as e:
                out.append(f"PLACED FILE: {placed_p} (failed to load: {e})")
        else:
            out.append("PLACED: (none)")

        # Local import to avoid circular/startup issues in some packaged builds
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton
        dlg = QDialog(self)
        dlg.setWindowTitle("Plan Viewer (Draft + Placed)")
        dlg.resize(900, 650)
        lay = QVBoxLayout()
        editor = QTextEdit()
        editor.setReadOnly(True)
        editor.setLineWrapMode(QTextEdit.NoWrap)
        editor.setText("\n".join(out))
        lay.addWidget(editor)

        btns = QHBoxLayout()
        btns.addStretch(1)
        b_close = QPushButton("Close")
        b_close.clicked.connect(dlg.accept)
        btns.addWidget(b_close)
        lay.addLayout(btns)

        dlg.setLayout(lay)
        dlg.exec()

    def _on_compare_plans(self) -> None:
        sym = self.symbol_combo.currentText().strip()
        draft_p = latest_plan(sym, "draft")
        placed_p = latest_plan(sym, "placed")
        if not (draft_p and draft_p.exists()):
            QMessageBox.warning(self, "No draft", "No draft plan found for this symbol.")
            return
        if not (placed_p and placed_p.exists()):
            QMessageBox.warning(self, "No placed plan", "No placed plan found for this symbol.")
            return
        try:
            draft = load_json(draft_p)
            placed = load_json(placed_p)
        except Exception as e:
            QMessageBox.warning(self, "Load failed", str(e))
            return

        diff = compute_plan_diff(draft, placed)
        dlg = DiffDialog("Compare Draft vs Placed", diff, parent=self)
        dlg.exec()

    # --------------------- v1.0.2 Feature Methods ---------------------

    def _setup_auto_reconnect(self) -> None:
        """Setup auto-reconnect callbacks."""
        def do_connect() -> bool:
            try:
                mode = self.cfg["ibkr"]["mode"]
                port = int(self.cfg["ibkr"]["port_paper"] if mode == "paper" else self.cfg["ibkr"]["port_live"])
                host = self.cfg["ibkr"]["host"]
                client_id = int(self.cfg["ibkr"]["client_id"])
                self.ib.connect_and_start(host, port, client_id, timeout=Timeouts.IBKR_STANDARD)
                return self.ib.isConnected()
            except Exception:
                return False

        def is_connected() -> bool:
            return self.ib.isConnected() if self.ib else False

        def on_reconnect_success():
            self.logger.info("Auto-reconnect successful")
            self._sound_player.play(SOUND_CONNECT)
            QTimer.singleShot(0, lambda: self._connect_done({"net_liq": self.ib.get_net_liq(timeout=Timeouts.IBKR_STANDARD)}))

        def on_reconnect_failed(attempt: int):
            self.logger.warning(f"Auto-reconnect attempt {attempt} failed")

        def on_exhausted():
            self.logger.error("All auto-reconnect attempts exhausted")
            self._sound_player.play(SOUND_ERROR)
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Connection Lost", "Could not reconnect to IB Gateway after multiple attempts."))

        self._reconnect_manager.set_callbacks(
            connect=do_connect,
            is_connected=is_connected,
            on_success=on_reconnect_success,
            on_failed=on_reconnect_failed,
            on_exhausted=on_exhausted,
        )

    def _toggle_dark_mode(self, checked: bool) -> None:
        """Toggle dark mode on/off."""
        self._dark_mode_enabled = checked
        mode = ThemeMode.DARK if checked else ThemeMode.LIGHT
        apply_theme(mode)
        self.logger.info(f"Dark mode {'enabled' if checked else 'disabled'}")

    def _toggle_sound(self, checked: bool) -> None:
        """Toggle sound notifications."""
        self._sound_player.enabled = checked
        self.logger.info(f"Sound notifications {'enabled' if checked else 'disabled'}")

    def _toggle_minimize_to_tray(self, checked: bool) -> None:
        """Toggle minimize to tray behavior."""
        self._tray_manager.set_minimize_to_tray(checked)
        if checked and self._tray_manager.is_available:
            self._setup_tray_icon()
        self.logger.info(f"Minimize to tray {'enabled' if checked else 'disabled'}")

    def _setup_tray_icon(self) -> None:
        """Setup system tray icon."""
        if not self._tray_manager.is_available:
            return

        self._tray_manager.setup(self)
        self._tray_manager.set_show_callback(self._show_from_tray)
        self._tray_manager.set_quit_callback(self.close)
        self._tray_manager.show()

    def _show_from_tray(self) -> None:
        """Show window from tray."""
        self.show()
        self.raise_()
        self.activateWindow()

    def _show_trade_journal(self) -> None:
        """Show trade journal dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton, QLabel

        dlg = QDialog(self)
        dlg.setWindowTitle("Trade Journal")
        dlg.resize(900, 600)

        layout = QVBoxLayout()

        # Statistics summary
        stats = self._trade_journal.get_statistics()
        stats_text = (
            f"Total Trades: {stats['total_trades']} | "
            f"Open: {stats['open_trades']} | "
            f"Closed: {stats['closed_trades']} | "
            f"Win Rate: {stats['win_rate']:.1f}% | "
            f"Total P&L: ${stats['total_pnl']:,.2f}"
        )
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(stats_label)

        # Trades table
        trades = self._trade_journal.get_all_trades()
        table = QTableWidget(len(trades), 9)
        table.setHorizontalHeaderLabels([
            "ID", "Symbol", "Side", "Status", "Entry", "Exit", "Qty", "P&L", "R-Multiple"
        ])
        table.setAlternatingRowColors(True)

        for row, trade in enumerate(trades):
            items = [
                QTableWidgetItem(trade.id),
                QTableWidgetItem(trade.symbol),
                QTableWidgetItem(trade.side),
                QTableWidgetItem(trade.status),
                QTableWidgetItem(f"${trade.entry_price:.2f}"),
                QTableWidgetItem(f"${trade.exit_price:.2f}" if trade.exit_price else "--"),
                QTableWidgetItem(str(trade.quantity)),
                QTableWidgetItem(f"${trade.realized_pnl:+,.2f}" if trade.realized_pnl else "--"),
                QTableWidgetItem(f"{trade.r_multiple:.2f}R" if trade.r_multiple else "--"),
            ]
            for col, item in enumerate(items):
                table.setItem(row, col, item)

        layout.addWidget(table)

        # Buttons
        btns = QHBoxLayout()
        btn_export = QPushButton("Export to CSV")
        btn_export.clicked.connect(lambda: self._export_journal_csv())
        btns.addWidget(btn_export)
        btns.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.accept)
        btns.addWidget(btn_close)
        layout.addLayout(btns)

        dlg.setLayout(layout)
        dlg.exec()

    def _export_journal_csv(self) -> None:
        """Export trade journal to CSV."""
        from PySide6.QtWidgets import QFileDialog

        path, _ = QFileDialog.getSaveFileName(self, "Export Trade Journal", "trades.csv", "CSV Files (*.csv)")
        if path:
            if self._trade_journal.export_to_csv(Path(path)):
                QMessageBox.information(self, "Export Complete", f"Trades exported to:\n{path}")
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to export trades.")

    def _show_alerts(self) -> None:
        """Show alerts management dialog."""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QPushButton, QLabel, QDoubleSpinBox

        dlg = QDialog(self)
        dlg.setWindowTitle("Price Alerts")
        dlg.resize(700, 500)

        layout = QVBoxLayout()

        # Add alert section
        add_row = QHBoxLayout()
        add_row.addWidget(QLabel("Symbol:"))
        symbol_input = QLineEdit()
        symbol_input.setPlaceholderText("AAPL")
        symbol_input.setMaximumWidth(80)
        add_row.addWidget(symbol_input)

        add_row.addWidget(QLabel("Price:"))
        price_input = QDoubleSpinBox()
        price_input.setMaximum(1000000)
        price_input.setDecimals(2)
        add_row.addWidget(price_input)

        condition_combo = QComboBox()
        condition_combo.addItems(["Above", "Below", "Crosses Above", "Crosses Below"])
        add_row.addWidget(condition_combo)

        btn_add = QPushButton("Add Alert")
        add_row.addWidget(btn_add)
        add_row.addStretch()
        layout.addLayout(add_row)

        # Alerts table
        alerts = self._alert_manager.get_all_alerts()
        table = QTableWidget(len(alerts), 5)
        table.setHorizontalHeaderLabels(["ID", "Symbol", "Condition", "Price", "Status"])
        table.setAlternatingRowColors(True)

        def refresh_table():
            alerts = self._alert_manager.get_all_alerts()
            table.setRowCount(len(alerts))
            for row, alert in enumerate(alerts):
                items = [
                    QTableWidgetItem(alert.id),
                    QTableWidgetItem(alert.symbol),
                    QTableWidgetItem(alert.condition),
                    QTableWidgetItem(f"${alert.price:.2f}"),
                    QTableWidgetItem(alert.status),
                ]
                for col, item in enumerate(items):
                    table.setItem(row, col, item)

        refresh_table()

        def add_alert():
            sym = symbol_input.text().strip().upper()
            price = price_input.value()
            cond_map = {
                "Above": AlertCondition.PRICE_ABOVE,
                "Below": AlertCondition.PRICE_BELOW,
                "Crosses Above": AlertCondition.PRICE_CROSSES_ABOVE,
                "Crosses Below": AlertCondition.PRICE_CROSSES_BELOW,
            }
            cond = cond_map.get(condition_combo.currentText(), AlertCondition.PRICE_ABOVE)
            if sym and price > 0:
                self._alert_manager.add_alert(sym, cond, price)
                refresh_table()
                symbol_input.clear()
                self.logger.info(f"Added alert: {sym} {cond.value} ${price:.2f}")

        btn_add.clicked.connect(add_alert)
        layout.addWidget(table)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(dlg.accept)
        btns.addWidget(btn_close)
        layout.addLayout(btns)

        dlg.setLayout(layout)
        dlg.exec()

    def _on_backup_settings(self) -> None:
        """Create a settings backup."""
        from ..core.config_backup import create_backup

        try:
            backup_path = create_backup(description="Manual backup")
            QMessageBox.information(self, "Backup Created", f"Settings backed up to:\n{backup_path}")
            self.logger.info(f"Settings backup created: {backup_path}")
        except Exception as e:
            QMessageBox.warning(self, "Backup Failed", f"Failed to create backup:\n{str(e)}")

    def _on_restore_settings(self) -> None:
        """Restore settings from a backup."""
        from PySide6.QtWidgets import QFileDialog
        from ..core.config_backup import restore_backup, get_backup_dir

        backup_dir = get_backup_dir()
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", str(backup_dir), "Backup Files (*.zip)"
        )

        if path:
            reply = QMessageBox.question(
                self, "Restore Backup",
                "This will overwrite your current settings.\n\nContinue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    results = restore_backup(Path(path))
                    self.cfg = load_config()  # Reload config
                    QMessageBox.information(
                        self, "Restore Complete",
                        f"Restored {len(results['restored_files'])} files.\n\nRestart the application to apply all changes."
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Restore Failed", f"Failed to restore backup:\n{str(e)}")

    def _check_for_updates(self) -> None:
        """Check for application updates."""
        self.logger.info("Checking for updates...")
        self.statusBar().showMessage("Checking for updates...", 3000)

        def on_result(info: Optional[UpdateInfo]):
            if info is None:
                QTimer.singleShot(0, lambda: QMessageBox.information(
                    self, "Update Check", "Could not check for updates.\nPlease try again later."
                ))
            elif info.is_update_available:
                QTimer.singleShot(0, lambda: self._show_update_available(info))
            else:
                QTimer.singleShot(0, lambda: QMessageBox.information(
                    self, "Up to Date",
                    f"You are running the latest version ({info.current_version})."
                ))

        check_for_updates_async(on_result)

    def _show_update_available(self, info: UpdateInfo) -> None:
        """Show update available dialog."""
        msg = QMessageBox(self)
        msg.setWindowTitle("Update Available")
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"<h3>A new version is available!</h3>")
        msg.setInformativeText(
            f"<b>Current:</b> {info.current_version}<br>"
            f"<b>Latest:</b> {info.latest_version}<br><br>"
            f"<b>Release Notes:</b><br>{info.release_notes[:500]}..."
        )

        download_btn = msg.addButton("Download", QMessageBox.ActionRole)
        msg.addButton(QMessageBox.Close)

        msg.exec()

        if msg.clickedButton() == download_btn:
            QDesktopServices.openUrl(QUrl(info.release_url))

    def changeEvent(self, event) -> None:
        """Handle window state changes for minimize to tray."""
        super().changeEvent(event)
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and self._tray_manager.minimize_to_tray_enabled:
                event.ignore()
                self.hide()
                self._tray_manager.show_notification(
                    "IBKRBot", "Application minimized to tray", "info"
                )