"""
Central constants module for IBKRBot.
Consolidates all magic numbers, timeouts, and configuration defaults.
"""
from datetime import datetime, time
from typing import Tuple


# ============================================================================
# Application Information
# ============================================================================
class AppInfo:
    """Application metadata and version information"""
    NAME = "IBKRBot"
    VERSION = "1.0.2"
    AUTHOR = "Joshua Metcalf"
    DESCRIPTION = "A swing trading assistant for Interactive Brokers (Paper and Live)"
    REPO_URL = "https://github.com/JrCheesey/IBKRBot"

    @staticmethod
    def get_full_name() -> str:
        """Get full application name with version"""
        return f"{AppInfo.NAME} v{AppInfo.VERSION}"

    @staticmethod
    def get_disclaimer() -> str:
        """Get legal disclaimer text"""
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


# ============================================================================
# Market Hours (US Eastern Time)
# ============================================================================
class MarketHours:
    """US stock market trading hours (Eastern Time)"""
    OPEN_HOUR = 9
    OPEN_MINUTE = 30
    CLOSE_HOUR = 16
    CLOSE_MINUTE = 0

    # Pre-market and after-hours
    PREMARKET_START_HOUR = 4
    AFTERHOURS_END_HOUR = 20

    @staticmethod
    def get_market_open() -> time:
        """Get market open time (9:30 AM ET)"""
        return time(MarketHours.OPEN_HOUR, MarketHours.OPEN_MINUTE)

    @staticmethod
    def get_market_close() -> time:
        """Get market close time (4:00 PM ET)"""
        return time(MarketHours.CLOSE_HOUR, MarketHours.CLOSE_MINUTE)

    @staticmethod
    def is_market_open(current_time: time = None) -> Tuple[bool, str]:
        """
        Check if US stock market is currently open (regular hours).

        Note: This is a simplified check. Does not account for:
        - Holidays
        - Early closes
        - Timezone conversions (assumes Eastern Time)

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            Tuple of (is_open, message)
        """
        if current_time is None:
            current_time = datetime.now().time()

        market_open = MarketHours.get_market_open()
        market_close = MarketHours.get_market_close()

        if current_time < market_open:
            return False, f"Market opens at {market_open.strftime('%H:%M')} ET"
        elif current_time >= market_close:
            return False, f"Market closed at {market_close.strftime('%H:%M')} ET"
        else:
            return True, "Market is open"

    @staticmethod
    def is_extended_hours(current_time: time = None) -> Tuple[bool, str]:
        """
        Check if we're in extended trading hours (pre-market or after-hours).

        Args:
            current_time: Time to check (defaults to now)

        Returns:
            Tuple of (is_extended, message)
        """
        if current_time is None:
            current_time = datetime.now().time()

        premarket_start = time(MarketHours.PREMARKET_START_HOUR, 0)
        market_open = MarketHours.get_market_open()
        market_close = MarketHours.get_market_close()
        afterhours_end = time(MarketHours.AFTERHOURS_END_HOUR, 0)

        if premarket_start <= current_time < market_open:
            return True, "Pre-market session"
        elif market_close <= current_time < afterhours_end:
            return True, "After-hours session"
        else:
            return False, "Outside extended hours"


# ============================================================================
# IBKR API Timeouts (seconds)
# ============================================================================
class Timeouts:
    """Timeout values for IBKR API calls"""
    IBKR_STANDARD = 6.0      # Standard operations (orders, positions, connection)
    IBKR_QUICK = 2.0         # Quick operations (manager polling)
    IBKR_ORDER_STATUS = 3.0  # Waiting for order status updates
    YFINANCE = 20.0          # Yahoo Finance data fetching


# ============================================================================
# IBKR Connection Defaults
# ============================================================================
class IBKRDefaults:
    """Default IBKR connection parameters"""
    PORT_PAPER = 4002
    PORT_LIVE = 4001
    HOST = "127.0.0.1"
    CLIENT_ID = 1


# ============================================================================
# Risk Management Defaults
# ============================================================================
class RiskDefaults:
    """Default risk limits and parameters"""
    MAX_NOTIONAL_PCT = 0.05   # 5% max position size
    MAX_LOSS_PCT = 0.005      # 0.5% max loss per trade
    MIN_RISK_PER_SHARE = 0.01 # Minimum risk per share
    R_MULTIPLE_TAKE = 2.0     # Take profit R-multiple
    EPSILON = 1e-6            # Float comparison tolerance


# ============================================================================
# Strategy Parameters
# ============================================================================
class StrategyDefaults:
    """Default strategy calculation parameters"""
    ATR_PERIOD = 14           # ATR lookback period
    CHART_MAX_BARS = 450      # Maximum bars for chart thumbnail
    CHART_DPI = 120           # Chart resolution
    TIME_IN_FORCE = "DAY"     # Default order TIF
    TIME_IN_FORCE_GTC = "GTC" # GTC time in force


# ============================================================================
# Janitor & Manager Settings
# ============================================================================
class AutomationDefaults:
    """Default settings for automated features"""
    JANITOR_EOD_THRESHOLD_MINUTES = 20  # Cancel orders X minutes before market close
    MANAGER_POLL_INTERVAL = 10          # Manager loop interval (seconds)
    MANAGER_SLEEP = 2.0                 # Manager quick sleep between operations


# ============================================================================
# Order Status Constants
# ============================================================================
class OrderStatus:
    """IBKR order status values"""
    FINAL_STATES = {"Cancelled", "Filled", "Inactive"}
    ACTIVE_STATES = {"Submitted", "PreSubmitted", "PendingSubmit", "PendingCancel"}

    CANCELLED = "Cancelled"
    FILLED = "Filled"
    INACTIVE = "Inactive"
    SUBMITTED = "Submitted"
    PRESUBMITTED = "PreSubmitted"


# ============================================================================
# Retry & Cancellation Settings
# ============================================================================
class RetryDefaults:
    """Default retry parameters"""
    CANCEL_MAX_RETRIES = 4
    CANCEL_RETRY_DELAY = 1.0  # seconds


# ============================================================================
# Logging Settings
# ============================================================================
class LoggingDefaults:
    """Default logging configuration"""
    MAX_LOG_BYTES = 10_000_000  # 10 MB
    BACKUP_COUNT = 5             # Keep 5 backup log files
    FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
