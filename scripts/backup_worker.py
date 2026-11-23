#!/usr/bin/env python3
"""Run recurring verified SQLite backups for the single-host pilot deployment."""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from scripts.sqlite_backup import BackupError, create_backup
except ModuleNotFoundError:  # Allow direct execution from scripts/.
    from sqlite_backup import BackupError, create_backup


DEFAULT_INTERVAL_SECONDS = 86400
DEFAULT_RETENTION_COUNT = 7
BACKUP_PREFIX = "aitv-production"


def positive_int(value: str | None, default: int, name: str) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        print(f"{name} must be a positive integer; using {default}.", file=sys.stderr)
        return default
    if parsed <= 0:
        print(f"{name} must be a positive integer; using {default}.", file=sys.stderr)
        return default
    return parsed


def prune_backups(directory: str | Path, keep: int) -> list[Path]:
    backup_dir = Path(directory)
    candidates = sorted(
        backup_dir.glob(f"{BACKUP_PREFIX}-*.sqlite3"),
        key=lambda path: path.name,
        reverse=True,
    )
    removed = candidates[keep:]
    for path in removed:
        path.unlink(missing_ok=True)
    return removed


def create_scheduled_backup(
    source: str | Path,
    directory: str | Path,
    *,
    keep: int = DEFAULT_RETENTION_COUNT,
    now: datetime | None = None,
) -> tuple[Path, list[Path]]:
    if keep <= 0:
        raise BackupError("Backup retention count must be greater than zero.")

    backup_dir = Path(directory).expanduser().resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)

    instant = now or datetime.now(timezone.utc)
    timestamp = instant.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = backup_dir / f"{BACKUP_PREFIX}-{timestamp}.sqlite3"
    created = create_backup(source, destination)
    removed = prune_backups(backup_dir, keep)
    return created, removed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--once",
        action="store_true",
        help="Create one backup and exit instead of running continuously.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    source = Path(os.getenv("SQLITE_DB_PATH", "/data/db.sqlite3"))
    directory = Path(os.getenv("BACKUP_DIRECTORY", "/backups"))
    interval = positive_int(
        os.getenv("BACKUP_INTERVAL_SECONDS"),
        DEFAULT_INTERVAL_SECONDS,
        "BACKUP_INTERVAL_SECONDS",
    )
    retention = positive_int(
        os.getenv("BACKUP_RETENTION_COUNT"),
        DEFAULT_RETENTION_COUNT,
        "BACKUP_RETENTION_COUNT",
    )

    while not source.is_file():
        if args.once:
            print(f"ERROR: SQLite database does not exist: {source}", file=sys.stderr)
            return 2
        time.sleep(2)

    while True:
        try:
            created, removed = create_scheduled_backup(
                source,
                directory,
                keep=retention,
            )
            print(f"Scheduled backup verified: {created}", flush=True)
            if removed:
                print(
                    f"Pruned {len(removed)} old backup(s); keeping newest {retention}.",
                    flush=True,
                )
        except (BackupError, OSError) as exc:
            print(f"Scheduled backup failed: {exc}", file=sys.stderr, flush=True)
            if args.once:
                return 2

        if args.once:
            return 0
        time.sleep(interval)


if __name__ == "__main__":
    raise SystemExit(main())
