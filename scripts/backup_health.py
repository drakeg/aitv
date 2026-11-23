#!/usr/bin/env python3
"""Report whether scheduled pilot backups are recent and still valid."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from scripts.backup_worker import BACKUP_PREFIX, DEFAULT_INTERVAL_SECONDS, positive_int
from scripts.sqlite_backup import BackupError, verify_database


DEFAULT_HEALTH_GRACE_SECONDS = 3600


def max_backup_age_seconds() -> int:
    interval = positive_int(
        os.getenv("BACKUP_INTERVAL_SECONDS"),
        DEFAULT_INTERVAL_SECONDS,
        "BACKUP_INTERVAL_SECONDS",
    )
    default_max_age = interval + DEFAULT_HEALTH_GRACE_SECONDS
    return positive_int(
        os.getenv("BACKUP_MAX_AGE_SECONDS"),
        default_max_age,
        "BACKUP_MAX_AGE_SECONDS",
    )


def newest_backup(directory: str | Path) -> Path:
    backup_dir = Path(directory).expanduser().resolve()
    candidates = list(backup_dir.glob(f"{BACKUP_PREFIX}-*.sqlite3"))
    if not candidates:
        raise BackupError(f"No scheduled backups found in {backup_dir}.")
    return max(candidates, key=lambda path: path.stat().st_mtime)


def check_backup_health(
    directory: str | Path,
    *,
    max_age_seconds: int,
    now: float | None = None,
) -> tuple[Path, int]:
    if max_age_seconds <= 0:
        raise BackupError("Backup maximum age must be greater than zero.")

    backup = newest_backup(directory)
    verify_database(backup)

    current_time = time.time() if now is None else now
    age_seconds = int(current_time - backup.stat().st_mtime)
    if age_seconds < 0:
        raise BackupError(
            f"Newest scheduled backup has a future modification time: {backup}"
        )
    if age_seconds > max_age_seconds:
        raise BackupError(
            f"Newest scheduled backup is stale ({age_seconds}s > "
            f"{max_age_seconds}s): {backup}"
        )
    return backup, age_seconds


def main() -> int:
    directory = Path(os.getenv("BACKUP_DIRECTORY", "/backups"))
    maximum_age = max_backup_age_seconds()
    try:
        backup, age_seconds = check_backup_health(
            directory,
            max_age_seconds=maximum_age,
        )
    except (BackupError, OSError) as exc:
        print(f"BACKUP UNHEALTHY: {exc}", file=sys.stderr)
        return 1

    print(f"BACKUP HEALTHY: {backup} age={age_seconds}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
