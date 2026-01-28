"""
Unit tests for Price Alerts module.
"""
import json
import pytest
import tempfile
from pathlib import Path

from ibkrbot.core.alerts import (
    AlertManager, PriceAlert, AlertCondition, AlertStatus
)


@pytest.fixture
def temp_alerts_file():
    """Create a temporary file for alerts storage."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        yield Path(f.name)


@pytest.fixture
def manager(temp_alerts_file):
    """Create an AlertManager instance with temporary storage."""
    return AlertManager(alerts_file=temp_alerts_file)


class TestPriceAlert:
    """Tests for PriceAlert dataclass."""

    def test_create_alert(self):
        """Test creating a price alert."""
        alert = PriceAlert(
            id="A001",
            symbol="AAPL",
            condition=AlertCondition.PRICE_ABOVE.value,
            price=150.00,
        )
        assert alert.id == "A001"
        assert alert.symbol == "AAPL"
        assert alert.is_active is True

    def test_alert_description(self):
        """Test alert description generation."""
        alert = PriceAlert(
            id="A001",
            symbol="AAPL",
            condition=AlertCondition.PRICE_ABOVE.value,
            price=150.00,
        )
        desc = alert.get_description()
        assert "AAPL" in desc
        assert "150.00" in desc

    def test_check_condition_price_above(self):
        """Test price above condition."""
        alert = PriceAlert(
            id="A001",
            symbol="AAPL",
            condition=AlertCondition.PRICE_ABOVE.value,
            price=150.00,
        )
        assert alert.check_condition(149.00) is False
        assert alert.check_condition(150.00) is True
        assert alert.check_condition(151.00) is True

    def test_check_condition_price_below(self):
        """Test price below condition."""
        alert = PriceAlert(
            id="A001",
            symbol="AAPL",
            condition=AlertCondition.PRICE_BELOW.value,
            price=150.00,
        )
        assert alert.check_condition(151.00) is False
        assert alert.check_condition(150.00) is True
        assert alert.check_condition(149.00) is True

    def test_check_condition_crosses_above(self):
        """Test crosses above condition."""
        alert = PriceAlert(
            id="A001",
            symbol="AAPL",
            condition=AlertCondition.PRICE_CROSSES_ABOVE.value,
            price=150.00,
        )
        # First check - no previous price
        assert alert.check_condition(149.00) is False

        # Cross from below
        assert alert.check_condition(151.00) is True

        # Already above - no trigger
        assert alert.check_condition(152.00) is False

    def test_check_condition_crosses_below(self):
        """Test crosses below condition."""
        alert = PriceAlert(
            id="A001",
            symbol="AAPL",
            condition=AlertCondition.PRICE_CROSSES_BELOW.value,
            price=150.00,
        )
        # First check - no previous price
        assert alert.check_condition(151.00) is False

        # Cross from above
        assert alert.check_condition(149.00) is True

        # Already below - no trigger
        alert.last_price = 149.00
        assert alert.check_condition(148.00) is False


class TestAlertManager:
    """Tests for AlertManager class."""

    def test_add_alert(self, manager):
        """Test adding an alert."""
        alert = manager.add_alert(
            symbol="AAPL",
            condition=AlertCondition.PRICE_ABOVE,
            price=150.00,
            note="Breakout level",
        )
        assert alert.symbol == "AAPL"
        assert alert.id.startswith("A")

    def test_get_alert(self, manager):
        """Test getting an alert by ID."""
        alert = manager.add_alert("AAPL", AlertCondition.PRICE_ABOVE, 150.00)
        retrieved = manager.get_alert(alert.id)
        assert retrieved is not None
        assert retrieved.symbol == "AAPL"

    def test_remove_alert(self, manager):
        """Test removing an alert."""
        alert = manager.add_alert("AAPL", AlertCondition.PRICE_ABOVE, 150.00)
        assert manager.remove_alert(alert.id) is True
        assert manager.get_alert(alert.id) is None

    def test_get_alerts_for_symbol(self, manager):
        """Test getting alerts for a symbol."""
        manager.add_alert("AAPL", AlertCondition.PRICE_ABOVE, 150.00)
        manager.add_alert("AAPL", AlertCondition.PRICE_BELOW, 140.00)
        manager.add_alert("MSFT", AlertCondition.PRICE_ABOVE, 300.00)

        aapl_alerts = manager.get_alerts_for_symbol("AAPL")
        assert len(aapl_alerts) == 2

    def test_disable_enable_alert(self, manager):
        """Test disabling and enabling an alert."""
        alert = manager.add_alert("AAPL", AlertCondition.PRICE_ABOVE, 150.00)

        assert manager.disable_alert(alert.id) is True
        disabled = manager.get_alert(alert.id)
        assert disabled.status == AlertStatus.DISABLED.value

        assert manager.enable_alert(alert.id) is True
        enabled = manager.get_alert(alert.id)
        assert enabled.status == AlertStatus.ACTIVE.value

    def test_check_alerts_triggers(self, manager):
        """Test checking alerts and triggering."""
        manager.add_alert("AAPL", AlertCondition.PRICE_ABOVE, 150.00)

        # Price below threshold - no trigger
        triggered = manager.check_alerts("AAPL", 149.00)
        assert len(triggered) == 0

        # Price above threshold - trigger
        triggered = manager.check_alerts("AAPL", 151.00)
        assert len(triggered) == 1
        assert triggered[0].triggered_at is not None

    def test_repeating_alert(self, manager):
        """Test repeating alert."""
        alert = manager.add_alert(
            "AAPL", AlertCondition.PRICE_ABOVE, 150.00, repeat=True
        )

        # First trigger
        triggered = manager.check_alerts("AAPL", 151.00)
        assert len(triggered) == 1

        # Should still be active
        updated = manager.get_alert(alert.id)
        assert updated.is_active is True

    def test_non_repeating_alert(self, manager):
        """Test non-repeating alert becomes triggered status."""
        alert = manager.add_alert(
            "AAPL", AlertCondition.PRICE_ABOVE, 150.00, repeat=False
        )

        triggered = manager.check_alerts("AAPL", 151.00)
        assert len(triggered) == 1

        # Should be triggered status now
        updated = manager.get_alert(alert.id)
        assert updated.status == AlertStatus.TRIGGERED.value

    def test_callback_on_trigger(self, manager):
        """Test callback is called when alert triggers."""
        triggered_alerts = []

        def on_trigger(alert, price):
            triggered_alerts.append((alert, price))

        manager.register_callback(on_trigger)
        manager.add_alert("AAPL", AlertCondition.PRICE_ABOVE, 150.00)

        manager.check_alerts("AAPL", 151.00)

        assert len(triggered_alerts) == 1
        assert triggered_alerts[0][0].symbol == "AAPL"
        assert triggered_alerts[0][1] == 151.00

    def test_persistence(self, temp_alerts_file):
        """Test that alerts persist to disk."""
        # Create manager and add alert
        m1 = AlertManager(alerts_file=temp_alerts_file)
        alert = m1.add_alert("AAPL", AlertCondition.PRICE_ABOVE, 150.00)

        # Create new manager instance (simulates restart)
        m2 = AlertManager(alerts_file=temp_alerts_file)
        loaded = m2.get_alert(alert.id)

        assert loaded is not None
        assert loaded.symbol == "AAPL"

    def test_case_insensitive_symbol(self, manager):
        """Test symbol handling is case-insensitive."""
        manager.add_alert("aapl", AlertCondition.PRICE_ABOVE, 150.00)

        alerts = manager.get_alerts_for_symbol("AAPL")
        assert len(alerts) == 1

        alerts = manager.get_alerts_for_symbol("aapl")
        assert len(alerts) == 1
