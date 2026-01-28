"""Update checker - queries GitHub releases."""
from __future__ import annotations
import logging
import threading
from typing import Optional, Tuple, Callable
from dataclasses import dataclass

from .constants import AppInfo

_log = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/repos/JrCheesey/IBKRBot/releases/latest"


@dataclass
class UpdateInfo:
    current_version: str
    latest_version: str
    release_url: str
    release_notes: str
    is_update_available: bool


def parse_version(version: str) -> Tuple[int, ...]:
    """Parse version string like '1.0.2' into tuple (1, 0, 2)."""
    try:
        # Remove 'v' prefix if present
        version = version.lstrip('vV')
        return tuple(int(x) for x in version.split('.'))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def is_newer_version(current: str, latest: str) -> bool:
    """Check if latest version is newer than current."""
    return parse_version(latest) > parse_version(current)


def check_for_updates(timeout: float = 10.0) -> Optional[UpdateInfo]:
    """
    Check GitHub for available updates.

    Args:
        timeout: Request timeout in seconds

    Returns:
        UpdateInfo if check successful, None if failed
    """
    try:
        import urllib.request
        import json

        _log.debug(f"Checking for updates at {GITHUB_API_URL}")

        request = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': f'IBKRBot/{AppInfo.VERSION}'
            }
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode('utf-8'))

        latest_version = data.get('tag_name', '').lstrip('vV')
        release_url = data.get('html_url', AppInfo.REPO_URL)
        release_notes = data.get('body', 'No release notes available.')

        current_version = AppInfo.VERSION
        update_available = is_newer_version(current_version, latest_version)

        info = UpdateInfo(
            current_version=current_version,
            latest_version=latest_version,
            release_url=release_url,
            release_notes=release_notes,
            is_update_available=update_available
        )

        if update_available:
            _log.info(f"Update available: {current_version} -> {latest_version}")
        else:
            _log.debug(f"No update available (current: {current_version}, latest: {latest_version})")

        return info

    except urllib.error.HTTPError as e:
        if e.code == 404:
            _log.debug("No releases found on GitHub")
        else:
            _log.warning(f"HTTP error checking for updates: {e.code}")
        return None
    except urllib.error.URLError as e:
        _log.debug(f"Network error checking for updates: {e}")
        return None
    except Exception as e:
        _log.warning(f"Error checking for updates: {e}")
        return None


def check_for_updates_async(
    callback: Callable[[Optional[UpdateInfo]], None],
    timeout: float = 10.0
) -> threading.Thread:
    """
    Check for updates asynchronously.

    Args:
        callback: Function to call with UpdateInfo result
        timeout: Request timeout in seconds

    Returns:
        The background thread
    """
    def _check():
        result = check_for_updates(timeout)
        callback(result)

    thread = threading.Thread(target=_check, daemon=True)
    thread.start()
    return thread


class UpdateChecker:
    def __init__(self, check_interval_hours: float = 24.0):
        self._interval = check_interval_hours * 3600  # Convert to seconds
        self._last_check: Optional[UpdateInfo] = None
        self._timer: Optional[threading.Timer] = None
        self._callback: Optional[Callable[[UpdateInfo], None]] = None
        self._running = False

    def start(self, callback: Callable[[UpdateInfo], None]) -> None:
        """Start periodic update checks."""
        self._callback = callback
        self._running = True
        self._schedule_check()
        _log.info(f"Update checker started (interval: {self._interval/3600:.1f} hours)")

    def stop(self) -> None:
        """Stop periodic update checks."""
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None
        _log.info("Update checker stopped")

    def check_now(self) -> None:
        """Trigger an immediate update check."""
        if self._callback:
            check_for_updates_async(self._on_check_complete)

    def _schedule_check(self) -> None:
        """Schedule the next update check."""
        if not self._running:
            return

        self._timer = threading.Timer(self._interval, self._do_check)
        self._timer.daemon = True
        self._timer.start()

    def _do_check(self) -> None:
        """Perform update check and reschedule."""
        if not self._running:
            return

        check_for_updates_async(self._on_check_complete)
        self._schedule_check()

    def _on_check_complete(self, info: Optional[UpdateInfo]) -> None:
        """Handle update check completion."""
        if info and info.is_update_available:
            self._last_check = info
            if self._callback:
                self._callback(info)

    @property
    def last_check(self) -> Optional[UpdateInfo]:
        """Get the result of the last update check."""
        return self._last_check
