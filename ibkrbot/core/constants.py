"""App constants and defaults."""
from datetime import datetime, time


class AppInfo:
    NAME = "IBKRBot"
    VERSION = "1.0.3"
    AUTHOR = "Joshua Metcalf"
    DESCRIPTION = "Swing trading assistant for Interactive Brokers"
    REPO_URL = "https://github.com/JrCheesey/IBKRBot"

    @staticmethod
    def get_full_name():
        return f"{AppInfo.NAME} v{AppInfo.VERSION}"

    @staticmethod
    def get_disclaimer():
        return """IMPORTANT DISCLAIMER:

This software is provided for EDUCATIONAL PURPOSES ONLY.

Trading stocks and other financial instruments involves substantial risk of loss.
Past performance does not guarantee future results. You should carefully consider
whether trading is suitable for you in light of your circumstances, knowledge,
and financial resources.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

The author is NOT a registered investment advisor and does NOT provide financial
advice. All trading decisions are made by the user at their own discretion.

USE AT YOUR OWN RISK. The author shall NOT be liable for any trading losses,
damages, or other liabilities incurred through the use of this software.

By using this software, you acknowledge that you have read and understood
this disclaimer and agree to its terms."""


class MarketHours:
    """US market hours (Eastern Time)."""
    OPEN = time(9, 30)
    CLOSE = time(16, 0)
    PREMARKET_START = time(4, 0)
    AFTERHOURS_END = time(20, 0)

    @staticmethod
    def is_open(t=None):
        t = t or datetime.now().time()
        if t < MarketHours.OPEN:
            return False, f"Opens {MarketHours.OPEN.strftime('%H:%M')} ET"
        if t >= MarketHours.CLOSE:
            return False, f"Closed {MarketHours.CLOSE.strftime('%H:%M')} ET"
        return True, "Market open"

    @staticmethod
    def is_extended(t=None):
        t = t or datetime.now().time()
        if MarketHours.PREMARKET_START <= t < MarketHours.OPEN:
            return True, "Pre-market"
        if MarketHours.CLOSE <= t < MarketHours.AFTERHOURS_END:
            return True, "After-hours"
        return False, "Regular/closed"


class Timeouts:
    IBKR_STANDARD = 6.0
    IBKR_QUICK = 2.0
    IBKR_ORDER_STATUS = 3.0
    YFINANCE = 20.0


class IBKRDefaults:
    PORT_PAPER = 4002
    PORT_LIVE = 4001
    HOST = "127.0.0.1"
    CLIENT_ID = 1


class RiskDefaults:
    MAX_NOTIONAL_PCT = 0.05
    MAX_LOSS_PCT = 0.005
    MIN_RISK_PER_SHARE = 0.01
    R_MULTIPLE_TAKE = 2.0
    EPSILON = 1e-6


class StrategyDefaults:
    ATR_PERIOD = 14
    CHART_MAX_BARS = 450
    CHART_DPI = 120
    TIF_DAY = "DAY"
    TIF_GTC = "GTC"


class AutomationDefaults:
    JANITOR_EOD_MINUTES = 20
    MANAGER_POLL_SEC = 10
    MANAGER_SLEEP = 2.0


class OrderStatus:
    FINAL = {"Cancelled", "Filled", "Inactive"}
    ACTIVE = {"Submitted", "PreSubmitted", "PendingSubmit", "PendingCancel"}
    # Keep these for backwards compat
    FINAL_STATES = FINAL
    ACTIVE_STATES = ACTIVE


class RetryDefaults:
    MAX_RETRIES = 4
    DELAY_SEC = 1.0


class LoggingDefaults:
    MAX_BYTES = 10_000_000
    BACKUP_COUNT = 5
    FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
