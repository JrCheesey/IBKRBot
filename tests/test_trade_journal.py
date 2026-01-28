"""
Unit tests for Trade Journal module.
"""
import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from ibkrbot.core.trade_journal import (
    TradeJournal, TradeEntry, TradeStatus, TradeSide
)


@pytest.fixture
def temp_journal_dir():
    """Create a temporary directory for journal storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def journal(temp_journal_dir):
    """Create a TradeJournal instance with temporary storage."""
    return TradeJournal(journal_dir=temp_journal_dir)


class TestTradeEntry:
    """Tests for TradeEntry dataclass."""

    def test_create_trade_entry(self):
        """Test creating a trade entry."""
        entry = TradeEntry(
            id="T001",
            symbol="AAPL",
            side="long",
            status="open",
            entry_time="2024-01-15T10:00:00Z",
            entry_price=150.00,
            quantity=100,
        )
        assert entry.id == "T001"
        assert entry.symbol == "AAPL"
        assert entry.side == "long"
        assert entry.is_open is True
        assert entry.is_closed is False

    def test_trade_entry_to_dict(self):
        """Test converting trade entry to dict."""
        entry = TradeEntry(
            id="T001",
            symbol="AAPL",
            side="long",
            status="open",
            entry_time="2024-01-15T10:00:00Z",
            entry_price=150.00,
            quantity=100,
            stop_price=145.00,
            take_profit_price=160.00,
        )
        d = entry.to_dict()
        assert d["id"] == "T001"
        assert d["symbol"] == "AAPL"
        assert d["entry_price"] == 150.00
        assert d["stop_price"] == 145.00

    def test_trade_entry_from_dict(self):
        """Test creating trade entry from dict."""
        data = {
            "id": "T001",
            "symbol": "AAPL",
            "side": "long",
            "status": "open",
            "entry_time": "2024-01-15T10:00:00Z",
            "entry_price": 150.00,
            "quantity": 100,
        }
        entry = TradeEntry.from_dict(data)
        assert entry.id == "T001"
        assert entry.symbol == "AAPL"
        assert entry.tags == []  # Default value

    def test_risk_per_share(self):
        """Test risk per share calculation."""
        entry = TradeEntry(
            id="T001",
            symbol="AAPL",
            side="long",
            status="open",
            entry_time="2024-01-15T10:00:00Z",
            entry_price=150.00,
            quantity=100,
            stop_price=145.00,
        )
        assert entry.risk_per_share == 5.00

    def test_r_multiple_winning_trade(self):
        """Test R-multiple calculation for winning trade."""
        entry = TradeEntry(
            id="T001",
            symbol="AAPL",
            side="long",
            status="closed",
            entry_time="2024-01-15T10:00:00Z",
            entry_price=150.00,
            quantity=100,
            stop_price=145.00,
            realized_pnl=1000.00,  # 2R profit
        )
        assert entry.r_multiple == 2.0

    def test_r_multiple_losing_trade(self):
        """Test R-multiple calculation for losing trade."""
        entry = TradeEntry(
            id="T001",
            symbol="AAPL",
            side="long",
            status="closed",
            entry_time="2024-01-15T10:00:00Z",
            entry_price=150.00,
            quantity=100,
            stop_price=145.00,
            realized_pnl=-500.00,  # 1R loss
        )
        assert entry.r_multiple == -1.0


class TestTradeJournal:
    """Tests for TradeJournal class."""

    def test_add_trade(self, journal):
        """Test adding a trade."""
        trade = journal.add_trade(
            symbol="AAPL",
            side="long",
            entry_price=150.00,
            quantity=100,
            stop_price=145.00,
            take_profit_price=160.00,
        )
        assert trade.symbol == "AAPL"
        assert trade.status == TradeStatus.OPEN.value
        assert trade.id.startswith("T")

    def test_get_trade(self, journal):
        """Test getting a trade by ID."""
        trade = journal.add_trade(
            symbol="AAPL",
            side="long",
            entry_price=150.00,
            quantity=100,
        )
        retrieved = journal.get_trade(trade.id)
        assert retrieved is not None
        assert retrieved.symbol == "AAPL"

    def test_close_trade(self, journal):
        """Test closing a trade."""
        trade = journal.add_trade(
            symbol="AAPL",
            side="long",
            entry_price=150.00,
            quantity=100,
            stop_price=145.00,
        )
        closed = journal.close_trade(
            trade.id,
            exit_price=160.00,
        )
        assert closed is not None
        assert closed.status == TradeStatus.CLOSED.value
        assert closed.realized_pnl == 1000.00  # (160-150) * 100

    def test_close_short_trade(self, journal):
        """Test closing a short trade."""
        trade = journal.add_trade(
            symbol="AAPL",
            side="short",
            entry_price=150.00,
            quantity=100,
        )
        closed = journal.close_trade(
            trade.id,
            exit_price=140.00,
        )
        assert closed.realized_pnl == 1000.00  # (150-140) * 100

    def test_cancel_trade(self, journal):
        """Test cancelling a trade."""
        trade = journal.add_trade(
            symbol="AAPL",
            side="long",
            entry_price=150.00,
            quantity=100,
        )
        cancelled = journal.cancel_trade(trade.id, reason="Test cancellation")
        assert cancelled is not None
        assert cancelled.status == TradeStatus.CANCELLED.value
        assert "Test cancellation" in cancelled.notes

    def test_get_open_trades(self, journal):
        """Test getting open trades."""
        journal.add_trade("AAPL", "long", 150.00, 100)
        journal.add_trade("MSFT", "long", 300.00, 50)
        trade3 = journal.add_trade("GOOGL", "long", 2500.00, 10)
        journal.close_trade(trade3.id, exit_price=2600.00)

        open_trades = journal.get_open_trades()
        assert len(open_trades) == 2

    def test_get_trades_by_symbol(self, journal):
        """Test getting trades by symbol."""
        journal.add_trade("AAPL", "long", 150.00, 100)
        journal.add_trade("AAPL", "long", 155.00, 50)
        journal.add_trade("MSFT", "long", 300.00, 50)

        aapl_trades = journal.get_trades_by_symbol("AAPL")
        assert len(aapl_trades) == 2

    def test_statistics_no_trades(self, journal):
        """Test statistics with no closed trades."""
        stats = journal.get_statistics()
        assert stats["total_trades"] == 0
        assert stats["win_rate"] == 0.0
        assert stats["total_pnl"] == 0.0

    def test_statistics_with_trades(self, journal):
        """Test statistics calculation."""
        # Winning trade
        t1 = journal.add_trade("AAPL", "long", 150.00, 100, stop_price=145.00)
        journal.close_trade(t1.id, exit_price=160.00)  # +$1000

        # Losing trade
        t2 = journal.add_trade("MSFT", "long", 300.00, 50, stop_price=290.00)
        journal.close_trade(t2.id, exit_price=290.00)  # -$500

        stats = journal.get_statistics()
        assert stats["closed_trades"] == 2
        assert stats["winners"] == 1
        assert stats["losers"] == 1
        assert stats["win_rate"] == 50.0
        assert stats["total_pnl"] == 500.00  # Net

    def test_persistence(self, temp_journal_dir):
        """Test that trades persist to disk."""
        # Create journal and add trade
        j1 = TradeJournal(journal_dir=temp_journal_dir)
        trade = j1.add_trade("AAPL", "long", 150.00, 100)

        # Create new journal instance (simulates restart)
        j2 = TradeJournal(journal_dir=temp_journal_dir)
        loaded = j2.get_trade(trade.id)

        assert loaded is not None
        assert loaded.symbol == "AAPL"

    def test_add_tag(self, journal):
        """Test adding tags to a trade."""
        trade = journal.add_trade("AAPL", "long", 150.00, 100)
        journal.add_tag(trade.id, "earnings")
        journal.add_tag(trade.id, "breakout")

        updated = journal.get_trade(trade.id)
        assert "earnings" in updated.tags
        assert "breakout" in updated.tags

    def test_update_notes(self, journal):
        """Test updating trade notes."""
        trade = journal.add_trade("AAPL", "long", 150.00, 100, notes="Initial note")
        journal.update_notes(trade.id, "Updated note with analysis")

        updated = journal.get_trade(trade.id)
        assert updated.notes == "Updated note with analysis"
