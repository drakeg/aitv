#!/usr/bin/env python3
"""Create, verify, and restore consistent SQLite backups for aitv.

The restore operation is intentionally guarded. It must only be used while
application writers are stopped.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


class BackupError(RuntimeError):
    """Raised when a backup or restore safety check fails."""


def _resolved(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def _read_only_connection(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)


def verify_database(path: str | Path) -> Path:
    database = _resolved(path)
    if not database.is_file():
        raise BackupError(f"SQLite database does not exist: {database}")
    if database.stat().st_size == 0:
        raise BackupError(f"SQLite database is empty: {database}")

    try:
        with _read_only_connection(database) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.DatabaseError as exc:
        raise BackupError(f"SQLite integrity check failed for {database}: {exc}") from exc

    if not result or result[0] != "ok":
        detail = result[0] if result else "no integrity result"
        raise BackupError(f"SQLite integrity check failed for {database}: {detail}")

    return database


def _sqlite_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.unlink(missing_ok=True)

    try:
        with _read_only_connection(source) as source_connection:
            with sqlite3.connect(temporary) as destination_connection:
                source_connection.backup(destination_connection)
        verify_database(temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def create_backup(source: str | Path, destination: str | Path) -> Path:
    source_path = verify_database(source)
    destination_path = _resolved(destination)

    if source_path == destination_path:
        raise BackupError("Backup destination must differ from the source database.")

    _sqlite_copy(source_path, destination_path)
    return verify_database(destination_path)


def restore_backup(
    backup: str | Path,
    target: str | Path,
    *,
    confirm_offline: bool = False,
) -> tuple[Path, Path | None]:
    if not confirm_offline:
        raise BackupError(
            "Restore refused: stop web/EPG/notification writers and pass "
            "--confirm-offline."
        )

    backup_path = verify_database(backup)
    target_path = _resolved(target)
    if backup_path == target_path:
        raise BackupError("Restore source must differ from the target database.")

    target_path.parent.mkdir(parents=True, exist_ok=True)

    pre_restore: Path | None = None
    if target_path.exists():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        pre_restore = target_path.with_name(
            f"{target_path.stem}.pre-restore-{timestamp}{target_path.suffix}"
        )
        create_backup(target_path, pre_restore)

    restore_staging = target_path.with_name(f".{target_path.name}.restore")
    restore_staging.unlink(missing_ok=True)

    try:
        _sqlite_copy(backup_path, restore_staging)
        verify_database(restore_staging)

        for suffix in ("-wal", "-shm"):
            Path(f"{target_path}{suffix}").unlink(missing_ok=True)

        os.replace(restore_staging, target_path)
    finally:
        restore_staging.unlink(missing_ok=True)

    return verify_database(target_path), pre_restore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup_parser = subparsers.add_parser(
        "backup", help="Create and verify a consistent SQLite backup."
    )
    backup_parser.add_argument("--source", required=True)
    backup_parser.add_argument("--output", required=True)

    verify_parser = subparsers.add_parser(
        "verify", help="Run SQLite integrity_check against a backup."
    )
    verify_parser.add_argument("--input", required=True)

    restore_parser = subparsers.add_parser(
        "restore", help="Restore a verified backup to an offline SQLite target."
    )
    restore_parser.add_argument("--input", required=True)
    restore_parser.add_argument("--target", required=True)
    restore_parser.add_argument(
        "--confirm-offline",
        action="store_true",
        help="Confirm all application writers have been stopped.",
    )

    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "backup":
            output = create_backup(args.source, args.output)
            print(f"Backup verified: {output}")
        elif args.command == "verify":
            verified = verify_database(args.input)
            print(f"Backup verified: {verified}")
        else:
            restored, pre_restore = restore_backup(
                args.input,
                args.target,
                confirm_offline=args.confirm_offline,
            )
            print(f"Restore verified: {restored}")
            if pre_restore:
                print(f"Pre-restore safety backup: {pre_restore}")
    except BackupError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
