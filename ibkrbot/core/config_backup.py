"""
Configuration backup and restore for IBKRBot.
Allows users to backup and restore their settings.
"""
from __future__ import annotations
import json
import logging
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import user_data_dir

_log = logging.getLogger(__name__)


def get_backup_dir() -> Path:
    """Get the backup directory path."""
    backup_dir = user_data_dir() / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def list_backups() -> List[Dict[str, Any]]:
    """List all available backups, sorted by date (newest first)."""
    backup_dir = get_backup_dir()
    backups = []

    for f in backup_dir.glob("backup_*.zip"):
        try:
            # Parse timestamp from filename: backup_YYYYMMDD_HHMMSS.zip
            name = f.stem
            parts = name.replace("backup_", "").split("_")
            if len(parts) >= 2:
                date_str = parts[0]
                time_str = parts[1]
                timestamp = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            else:
                timestamp = datetime.fromtimestamp(f.stat().st_mtime)

            backups.append({
                "path": f,
                "filename": f.name,
                "timestamp": timestamp,
                "size_bytes": f.stat().st_size,
                "size_human": _format_size(f.stat().st_size),
            })
        except Exception as e:
            _log.warning(f"Could not parse backup file {f}: {e}")
            continue

    # Sort by timestamp, newest first
    backups.sort(key=lambda x: x["timestamp"], reverse=True)
    return backups


def _format_size(size_bytes: int) -> str:
    """Format size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def create_backup(description: str = "") -> Path:
    """
    Create a backup of user configuration and data.

    Args:
        description: Optional description for the backup

    Returns:
        Path to the created backup file
    """
    user_dir = user_data_dir()
    backup_dir = get_backup_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.zip"
    backup_path = backup_dir / backup_name

    # Files to include in backup
    files_to_backup = [
        "config.json",
        "journal/trades.json",
        "alerts.json",
    ]

    # Directories to include
    dirs_to_backup = [
        "plans",
    ]

    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add metadata
        metadata = {
            "created_at": datetime.now().isoformat(),
            "description": description,
            "version": "1.0.2",
        }
        zf.writestr("backup_metadata.json", json.dumps(metadata, indent=2))

        # Add individual files
        for filename in files_to_backup:
            file_path = user_dir / filename
            if file_path.exists():
                zf.write(file_path, filename)
                _log.debug(f"Added {filename} to backup")

        # Add directories
        for dirname in dirs_to_backup:
            dir_path = user_dir / dirname
            if dir_path.exists() and dir_path.is_dir():
                for file in dir_path.rglob("*"):
                    if file.is_file():
                        rel_path = file.relative_to(user_dir)
                        zf.write(file, str(rel_path))
                        _log.debug(f"Added {rel_path} to backup")

    _log.info(f"Created backup: {backup_path}")
    return backup_path


def restore_backup(backup_path: Path, restore_config: bool = True,
                   restore_journal: bool = True, restore_plans: bool = True) -> Dict[str, Any]:
    """
    Restore from a backup file.

    Args:
        backup_path: Path to the backup ZIP file
        restore_config: Whether to restore config.json
        restore_journal: Whether to restore trade journal
        restore_plans: Whether to restore plans directory

    Returns:
        Dict with restoration results
    """
    user_dir = user_data_dir()
    results = {
        "restored_files": [],
        "skipped_files": [],
        "errors": [],
    }

    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    with zipfile.ZipFile(backup_path, 'r') as zf:
        for member in zf.namelist():
            # Skip metadata file
            if member == "backup_metadata.json":
                continue

            # Determine if we should restore this file
            should_restore = False
            if member == "config.json" and restore_config:
                should_restore = True
            elif member.startswith("journal/") and restore_journal:
                should_restore = True
            elif member.startswith("plans/") and restore_plans:
                should_restore = True
            elif member == "alerts.json" and restore_config:
                should_restore = True

            if should_restore:
                try:
                    target_path = user_dir / member
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # Extract file
                    with zf.open(member) as src:
                        with open(target_path, 'wb') as dst:
                            dst.write(src.read())

                    results["restored_files"].append(member)
                    _log.debug(f"Restored: {member}")
                except Exception as e:
                    results["errors"].append(f"{member}: {str(e)}")
                    _log.error(f"Failed to restore {member}: {e}")
            else:
                results["skipped_files"].append(member)

    _log.info(f"Restored {len(results['restored_files'])} files from backup")
    return results


def get_backup_metadata(backup_path: Path) -> Optional[Dict[str, Any]]:
    """Get metadata from a backup file."""
    try:
        with zipfile.ZipFile(backup_path, 'r') as zf:
            if "backup_metadata.json" in zf.namelist():
                with zf.open("backup_metadata.json") as f:
                    return json.loads(f.read().decode('utf-8'))
    except Exception as e:
        _log.warning(f"Could not read backup metadata: {e}")
    return None


def delete_backup(backup_path: Path) -> bool:
    """Delete a backup file."""
    try:
        if backup_path.exists():
            backup_path.unlink()
            _log.info(f"Deleted backup: {backup_path}")
            return True
    except Exception as e:
        _log.error(f"Failed to delete backup: {e}")
    return False


def cleanup_old_backups(keep_count: int = 10) -> int:
    """
    Clean up old backups, keeping only the most recent ones.

    Args:
        keep_count: Number of backups to keep

    Returns:
        Number of backups deleted
    """
    backups = list_backups()
    deleted = 0

    if len(backups) > keep_count:
        for backup in backups[keep_count:]:
            if delete_backup(backup["path"]):
                deleted += 1

    if deleted:
        _log.info(f"Cleaned up {deleted} old backups")

    return deleted
