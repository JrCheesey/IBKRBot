"""
Unit tests for Configuration Backup module.
"""
import json
import pytest
import tempfile
from pathlib import Path
import shutil

from ibkrbot.core.config_backup import (
    create_backup, restore_backup, list_backups,
    get_backup_metadata, delete_backup, cleanup_old_backups,
    get_backup_dir
)


@pytest.fixture
def temp_data_dir(monkeypatch):
    """Create a temporary data directory and mock user_data_dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir()

        # Mock user_data_dir to return our temp directory
        def mock_user_data_dir():
            return data_dir

        monkeypatch.setattr(
            "ibkrbot.core.config_backup.user_data_dir",
            mock_user_data_dir
        )

        yield data_dir


@pytest.fixture
def populated_data_dir(temp_data_dir):
    """Create a data directory with some content."""
    # Create config file
    config = {"setting1": "value1", "setting2": 42}
    config_path = temp_data_dir / "config.json"
    config_path.write_text(json.dumps(config))

    # Create journal
    journal_dir = temp_data_dir / "journal"
    journal_dir.mkdir()
    trades = {"trades": {"T001": {"symbol": "AAPL", "qty": 100}}}
    (journal_dir / "trades.json").write_text(json.dumps(trades))

    # Create plans directory
    plans_dir = temp_data_dir / "plans"
    plans_dir.mkdir()
    plan = {"symbol": "AAPL", "entry": 150.00}
    (plans_dir / "AAPL_draft.json").write_text(json.dumps(plan))

    return temp_data_dir


class TestCreateBackup:
    """Tests for backup creation."""

    def test_create_backup_basic(self, populated_data_dir):
        """Test creating a basic backup."""
        backup_path = create_backup(description="Test backup")

        assert backup_path.exists()
        assert backup_path.suffix == ".zip"
        assert backup_path.stat().st_size > 0

    def test_create_backup_includes_config(self, populated_data_dir):
        """Test backup includes config file."""
        import zipfile

        backup_path = create_backup()

        with zipfile.ZipFile(backup_path, 'r') as zf:
            names = zf.namelist()
            assert "config.json" in names

    def test_create_backup_includes_journal(self, populated_data_dir):
        """Test backup includes journal."""
        import zipfile

        backup_path = create_backup()

        with zipfile.ZipFile(backup_path, 'r') as zf:
            names = zf.namelist()
            assert any("journal" in n for n in names)

    def test_create_backup_includes_plans(self, populated_data_dir):
        """Test backup includes plans."""
        import zipfile

        backup_path = create_backup()

        with zipfile.ZipFile(backup_path, 'r') as zf:
            names = zf.namelist()
            assert any("plans" in n for n in names)

    def test_create_backup_has_metadata(self, populated_data_dir):
        """Test backup includes metadata."""
        backup_path = create_backup(description="Test description")

        metadata = get_backup_metadata(backup_path)
        assert metadata is not None
        assert metadata["description"] == "Test description"
        assert "created_at" in metadata


class TestRestoreBackup:
    """Tests for backup restoration."""

    def test_restore_full_backup(self, populated_data_dir):
        """Test restoring a full backup."""
        # Create backup
        backup_path = create_backup()

        # Modify files
        config_path = populated_data_dir / "config.json"
        config_path.write_text(json.dumps({"modified": True}))

        # Restore
        results = restore_backup(backup_path)

        assert len(results["restored_files"]) > 0
        assert len(results["errors"]) == 0

        # Check config was restored
        restored_config = json.loads(config_path.read_text())
        assert restored_config.get("setting1") == "value1"

    def test_restore_config_only(self, populated_data_dir):
        """Test restoring only config."""
        backup_path = create_backup()

        results = restore_backup(
            backup_path,
            restore_config=True,
            restore_journal=False,
            restore_plans=False
        )

        # Should only have config in restored files
        assert "config.json" in results["restored_files"]
        assert not any("journal" in f for f in results["restored_files"])

    def test_restore_nonexistent_backup(self, temp_data_dir):
        """Test restoring nonexistent backup raises error."""
        fake_path = temp_data_dir / "nonexistent.zip"

        with pytest.raises(FileNotFoundError):
            restore_backup(fake_path)


class TestListBackups:
    """Tests for listing backups."""

    def test_list_empty(self, temp_data_dir):
        """Test listing when no backups exist."""
        backups = list_backups()
        assert backups == []

    def test_list_multiple_backups(self, populated_data_dir):
        """Test listing multiple backups."""
        import time

        # Create multiple backups with sufficient delay for unique timestamps
        create_backup()
        time.sleep(1.1)  # Sleep > 1 second to ensure different second-resolution timestamps
        create_backup()

        backups = list_backups()
        assert len(backups) == 2

        # Should be sorted newest first
        assert backups[0]["timestamp"] >= backups[1]["timestamp"]

    def test_list_includes_size(self, populated_data_dir):
        """Test backup list includes size info."""
        create_backup()

        backups = list_backups()
        assert backups[0]["size_bytes"] > 0
        assert "size_human" in backups[0]


class TestDeleteBackup:
    """Tests for backup deletion."""

    def test_delete_backup(self, populated_data_dir):
        """Test deleting a backup."""
        backup_path = create_backup()
        assert backup_path.exists()

        result = delete_backup(backup_path)
        assert result is True
        assert not backup_path.exists()

    def test_delete_nonexistent(self, temp_data_dir):
        """Test deleting nonexistent backup."""
        fake_path = temp_data_dir / "nonexistent.zip"
        result = delete_backup(fake_path)
        assert result is False


class TestCleanupBackups:
    """Tests for backup cleanup."""

    def test_cleanup_keeps_recent(self, populated_data_dir):
        """Test cleanup keeps specified number of backups."""
        import time

        # Create several backups with unique timestamps
        for i in range(5):
            create_backup()
            if i < 4:  # Don't sleep after last one
                time.sleep(1.1)  # Sleep > 1 second for unique timestamps

        # Should have 5 backups
        assert len(list_backups()) == 5

        # Cleanup, keep only 3
        deleted = cleanup_old_backups(keep_count=3)

        assert deleted == 2
        assert len(list_backups()) == 3

    def test_cleanup_no_delete_needed(self, populated_data_dir):
        """Test cleanup when fewer backups than limit."""
        create_backup()

        deleted = cleanup_old_backups(keep_count=5)

        assert deleted == 0
        assert len(list_backups()) == 1
