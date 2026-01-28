"""
Unit tests for Update Checker module.
"""
import pytest
from unittest.mock import patch, MagicMock
import json

from ibkrbot.core.update_checker import (
    parse_version, is_newer_version, check_for_updates,
    UpdateInfo, UpdateChecker
)


class TestVersionParsing:
    """Tests for version parsing functions."""

    def test_parse_simple_version(self):
        """Test parsing simple version strings."""
        assert parse_version("1.0.0") == (1, 0, 0)
        assert parse_version("2.3.4") == (2, 3, 4)
        assert parse_version("10.20.30") == (10, 20, 30)

    def test_parse_version_with_prefix(self):
        """Test parsing versions with v prefix."""
        assert parse_version("v1.0.0") == (1, 0, 0)
        assert parse_version("V2.3.4") == (2, 3, 4)

    def test_parse_invalid_version(self):
        """Test parsing invalid versions returns default."""
        assert parse_version("invalid") == (0, 0, 0)
        assert parse_version("") == (0, 0, 0)
        assert parse_version(None) == (0, 0, 0)

    def test_is_newer_version_true(self):
        """Test is_newer_version when latest is newer."""
        assert is_newer_version("1.0.0", "1.0.1") is True
        assert is_newer_version("1.0.0", "1.1.0") is True
        assert is_newer_version("1.0.0", "2.0.0") is True
        assert is_newer_version("1.9.9", "2.0.0") is True

    def test_is_newer_version_false(self):
        """Test is_newer_version when current is same or newer."""
        assert is_newer_version("1.0.0", "1.0.0") is False
        assert is_newer_version("1.0.1", "1.0.0") is False
        assert is_newer_version("2.0.0", "1.9.9") is False


class TestUpdateInfo:
    """Tests for UpdateInfo dataclass."""

    def test_create_update_info(self):
        """Test creating UpdateInfo."""
        info = UpdateInfo(
            current_version="1.0.0",
            latest_version="1.0.1",
            release_url="https://example.com/release",
            release_notes="Bug fixes",
            is_update_available=True
        )
        assert info.current_version == "1.0.0"
        assert info.latest_version == "1.0.1"
        assert info.is_update_available is True


class TestCheckForUpdates:
    """Tests for check_for_updates function."""

    @patch('urllib.request.urlopen')
    def test_check_for_updates_newer_available(self, mock_urlopen):
        """Test check when newer version is available."""
        # Mock response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "tag_name": "v99.0.0",  # Very high version
            "html_url": "https://github.com/test/release",
            "body": "Release notes here"
        }).encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = check_for_updates()

        assert result is not None
        assert result.is_update_available is True
        assert result.latest_version == "99.0.0"

    @patch('urllib.request.urlopen')
    def test_check_for_updates_no_newer(self, mock_urlopen):
        """Test check when no newer version is available."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "tag_name": "v0.0.1",  # Very low version
            "html_url": "https://github.com/test/release",
            "body": "Release notes"
        }).encode('utf-8')
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = check_for_updates()

        assert result is not None
        assert result.is_update_available is False

    @patch('urllib.request.urlopen')
    def test_check_for_updates_network_error(self, mock_urlopen):
        """Test check handles network errors gracefully."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Network error")

        result = check_for_updates()

        assert result is None

    @patch('urllib.request.urlopen')
    def test_check_for_updates_404(self, mock_urlopen):
        """Test check handles 404 errors (no releases)."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "url", 404, "Not Found", {}, None
        )

        result = check_for_updates()

        assert result is None


class TestUpdateChecker:
    """Tests for UpdateChecker class."""

    def test_create_checker(self):
        """Test creating an UpdateChecker."""
        checker = UpdateChecker(check_interval_hours=24.0)
        assert checker._interval == 24.0 * 3600

    def test_start_stop_checker(self):
        """Test starting and stopping the checker."""
        checker = UpdateChecker()
        callback_called = []

        def callback(info):
            callback_called.append(info)

        checker.start(callback)
        assert checker._running is True

        checker.stop()
        assert checker._running is False

    def test_last_check_property(self):
        """Test last_check property."""
        checker = UpdateChecker()
        assert checker.last_check is None

        # Simulate a check result
        info = UpdateInfo(
            current_version="1.0.0",
            latest_version="1.0.1",
            release_url="https://example.com",
            release_notes="Notes",
            is_update_available=True
        )
        checker._last_check = info

        assert checker.last_check == info
