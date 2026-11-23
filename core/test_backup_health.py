import os
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

from scripts.backup_health import (
    DEFAULT_HEALTH_GRACE_SECONDS,
    check_backup_health,
    max_backup_age_seconds,
    newest_backup,
)
from scripts.backup_worker import BACKUP_PREFIX
from scripts.sqlite_backup import BackupError


class BackupHealthTests(SimpleTestCase):
    def _database(self, path: Path, value: str = "pilot-data") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE sample (value TEXT NOT NULL)")
            connection.execute("INSERT INTO sample (value) VALUES (?)", (value,))
            connection.commit()

    def test_newest_backup_ignores_unrelated_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / f"{BACKUP_PREFIX}-old.sqlite3"
            new = root / f"{BACKUP_PREFIX}-new.sqlite3"
            unrelated = root / "manual.sqlite3"
            self._database(old)
            self._database(new)
            unrelated.write_bytes(b"unrelated")
            os.utime(old, (100, 100))
            os.utime(new, (200, 200))
            os.utime(unrelated, (300, 300))

            self.assertEqual(newest_backup(root), new.resolve())

    def test_newest_backup_requires_worker_owned_backup(self):
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(BackupError, "No scheduled backups found"):
                newest_backup(directory)

    def test_health_verifies_integrity_and_freshness(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            backup = root / f"{BACKUP_PREFIX}-good.sqlite3"
            self._database(backup)
            os.utime(backup, (900, 900))

            healthy, age = check_backup_health(
                root,
                max_age_seconds=200,
                now=1000,
            )

            self.assertEqual(healthy, backup.resolve())
            self.assertEqual(age, 100)

    def test_health_rejects_stale_backup(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            backup = root / f"{BACKUP_PREFIX}-stale.sqlite3"
            self._database(backup)
            os.utime(backup, (100, 100))

            with self.assertRaisesRegex(BackupError, "stale"):
                check_backup_health(root, max_age_seconds=100, now=500)

    def test_health_rejects_corrupt_backup(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            backup = root / f"{BACKUP_PREFIX}-corrupt.sqlite3"
            backup.write_bytes(b"not sqlite")
            os.utime(backup, (900, 900))

            with self.assertRaisesRegex(BackupError, "integrity check failed"):
                check_backup_health(root, max_age_seconds=200, now=1000)

    def test_health_rejects_future_timestamp(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            backup = root / f"{BACKUP_PREFIX}-future.sqlite3"
            self._database(backup)
            os.utime(backup, (1100, 1100))

            with self.assertRaisesRegex(BackupError, "future modification time"):
                check_backup_health(root, max_age_seconds=200, now=1000)

    def test_default_max_age_tracks_interval_plus_grace(self):
        with patch.dict(os.environ, {"BACKUP_INTERVAL_SECONDS": "7200"}, clear=False):
            os.environ.pop("BACKUP_MAX_AGE_SECONDS", None)
            self.assertEqual(
                max_backup_age_seconds(),
                7200 + DEFAULT_HEALTH_GRACE_SECONDS,
            )

    def test_explicit_max_age_override_is_respected(self):
        with patch.dict(
            os.environ,
            {
                "BACKUP_INTERVAL_SECONDS": "7200",
                "BACKUP_MAX_AGE_SECONDS": "10000",
            },
            clear=False,
        ):
            self.assertEqual(max_backup_age_seconds(), 10000)
