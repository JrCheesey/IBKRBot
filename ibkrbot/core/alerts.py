"""Price alerts for IBKRBot."""
from __future__ import annotations
import json
import logging
import threading
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .paths import user_data_dir

_log = logging.getLogger(__name__)


class AlertCondition(Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PRICE_CROSSES_ABOVE = "crosses_above"
    PRICE_CROSSES_BELOW = "crosses_below"


class AlertStatus(Enum):
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    DISABLED = "disabled"


@dataclass
class PriceAlert:
    id: str
    symbol: str
    condition: str  # AlertCondition value
    price: float
    status: str = AlertStatus.ACTIVE.value
    created_at: str = ""
    triggered_at: Optional[str] = None
    expires_at: Optional[str] = None
    note: str = ""
    repeat: bool = False  # If True, alert resets after triggering
    last_price: Optional[float] = None  # For cross detection

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PriceAlert':
        return cls(**data)

    @property
    def is_active(self) -> bool:
        return self.status == AlertStatus.ACTIVE.value

    def check_condition(self, current_price: float) -> bool:
        """Check if alert condition is met."""
        if not self.is_active:
            return False

        condition = AlertCondition(self.condition)

        if condition == AlertCondition.PRICE_ABOVE:
            triggered = current_price >= self.price
        elif condition == AlertCondition.PRICE_BELOW:
            triggered = current_price <= self.price
        elif condition == AlertCondition.PRICE_CROSSES_ABOVE:
            # Need previous price to detect crossing
            if self.last_price is None:
                triggered = False
            else:
                triggered = self.last_price < self.price <= current_price
        elif condition == AlertCondition.PRICE_CROSSES_BELOW:
            if self.last_price is None:
                triggered = False
            else:
                triggered = self.last_price > self.price >= current_price
        else:
            triggered = False

        # Update last price for cross detection
        self.last_price = current_price

        return triggered

    def get_description(self) -> str:
        """Get human-readable description of the alert."""
        condition = AlertCondition(self.condition)
        cond_text = {
            AlertCondition.PRICE_ABOVE: "rises to",
            AlertCondition.PRICE_BELOW: "falls to",
            AlertCondition.PRICE_CROSSES_ABOVE: "crosses above",
            AlertCondition.PRICE_CROSSES_BELOW: "crosses below",
        }.get(condition, "reaches")

        return f"{self.symbol} {cond_text} ${self.price:.2f}"


class AlertManager:
    def __init__(self, alerts_file: Optional[Path] = None):
        if alerts_file is None:
            alerts_file = user_data_dir() / "alerts.json"
        self._alerts_file = alerts_file
        self._alerts: Dict[str, PriceAlert] = {}
        self._callbacks: List[Callable[[PriceAlert, float], None]] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self._price_fetcher: Optional[Callable[[str], Optional[float]]] = None
        self._load()

    def _load(self) -> None:
        """Load alerts from disk."""
        if self._alerts_file.exists():
            try:
                with open(self._alerts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for alert_id, alert_data in data.get('alerts', {}).items():
                    self._alerts[alert_id] = PriceAlert.from_dict(alert_data)
                _log.info(f"Loaded {len(self._alerts)} alerts")
            except Exception as e:
                _log.error(f"Error loading alerts: {e}")

    def _save(self) -> None:
        """Save alerts to disk."""
        try:
            data = {
                'version': '1.0',
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'alerts': {aid: a.to_dict() for aid, a in self._alerts.items()}
            }
            self._alerts_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._alerts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            _log.error(f"Error saving alerts: {e}")

    def _generate_id(self) -> str:
        """Generate unique alert ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        count = len(self._alerts) + 1
        return f"A{timestamp}_{count:04d}"

    def add_alert(
        self,
        symbol: str,
        condition: AlertCondition,
        price: float,
        note: str = "",
        repeat: bool = False,
        expires_at: Optional[str] = None,
    ) -> PriceAlert:
        """Add a new price alert."""
        alert_id = self._generate_id()
        alert = PriceAlert(
            id=alert_id,
            symbol=symbol.upper(),
            condition=condition.value,
            price=price,
            note=note,
            repeat=repeat,
            expires_at=expires_at,
        )
        self._alerts[alert_id] = alert
        self._save()
        _log.info(f"Added alert {alert_id}: {alert.get_description()}")
        return alert

    def remove_alert(self, alert_id: str) -> bool:
        """Remove an alert."""
        if alert_id in self._alerts:
            del self._alerts[alert_id]
            self._save()
            _log.info(f"Removed alert {alert_id}")
            return True
        return False

    def get_alert(self, alert_id: str) -> Optional[PriceAlert]:
        """Get alert by ID."""
        return self._alerts.get(alert_id)

    def get_all_alerts(self) -> List[PriceAlert]:
        """Get all alerts."""
        return list(self._alerts.values())

    def get_active_alerts(self) -> List[PriceAlert]:
        """Get all active alerts."""
        return [a for a in self._alerts.values() if a.is_active]

    def get_alerts_for_symbol(self, symbol: str) -> List[PriceAlert]:
        """Get alerts for a specific symbol."""
        return [a for a in self._alerts.values() if a.symbol == symbol.upper()]

    def disable_alert(self, alert_id: str) -> bool:
        """Disable an alert."""
        alert = self._alerts.get(alert_id)
        if alert:
            alert.status = AlertStatus.DISABLED.value
            self._save()
            return True
        return False

    def enable_alert(self, alert_id: str) -> bool:
        """Enable a disabled alert."""
        alert = self._alerts.get(alert_id)
        if alert and alert.status == AlertStatus.DISABLED.value:
            alert.status = AlertStatus.ACTIVE.value
            self._save()
            return True
        return False

    def register_callback(self, callback: Callable[[PriceAlert, float], None]) -> None:
        """Register a callback for when alerts trigger."""
        self._callbacks.append(callback)

    def check_alerts(self, symbol: str, current_price: float) -> List[PriceAlert]:
        """
        Check all alerts for a symbol against current price.
        Returns list of triggered alerts.
        """
        triggered = []

        for alert in self.get_alerts_for_symbol(symbol):
            if not alert.is_active:
                continue

            # Check expiration
            if alert.expires_at:
                try:
                    expires = datetime.fromisoformat(alert.expires_at)
                    if datetime.now(timezone.utc) > expires:
                        alert.status = AlertStatus.EXPIRED.value
                        continue
                except Exception:
                    pass

            if alert.check_condition(current_price):
                alert.triggered_at = datetime.now(timezone.utc).isoformat()

                if alert.repeat:
                    # Reset for next trigger
                    alert.last_price = None
                else:
                    alert.status = AlertStatus.TRIGGERED.value

                triggered.append(alert)

                # Call callbacks
                for callback in self._callbacks:
                    try:
                        callback(alert, current_price)
                    except Exception as e:
                        _log.error(f"Alert callback error: {e}")

                _log.info(f"Alert triggered: {alert.get_description()} at ${current_price:.2f}")

        if triggered:
            self._save()

        return triggered

    def set_price_fetcher(self, fetcher: Callable[[str], Optional[float]]) -> None:
        """Set the function used to fetch current prices."""
        self._price_fetcher = fetcher

    def start_monitoring(self, interval_seconds: float = 60.0) -> None:
        """Start background monitoring of alerts."""
        if self._monitor_thread is not None:
            return

        if self._price_fetcher is None:
            _log.warning("No price fetcher set, cannot start monitoring")
            return

        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, args=(interval_seconds,), daemon=True)
        self._monitor_thread.start()
        _log.info(f"Alert monitoring started (interval: {interval_seconds}s)")

    def stop_monitoring(self) -> None:
        """Stop background monitoring."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None
        _log.info("Alert monitoring stopped")

    def _monitor_loop(self, interval: float) -> None:
        """Background monitoring loop."""
        while self._running:
            active_alerts = self.get_active_alerts()

            # Get unique symbols
            symbols = set(a.symbol for a in active_alerts)

            for symbol in symbols:
                try:
                    price = self._price_fetcher(symbol)
                    if price is not None:
                        self.check_alerts(symbol, price)
                except Exception as e:
                    _log.debug(f"Error fetching price for {symbol}: {e}")

            # Sleep in small increments to allow quick shutdown
            for _ in range(int(interval)):
                if not self._running:
                    break
                time.sleep(1)


# Global instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
