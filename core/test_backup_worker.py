import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from scripts.backup_worker import (
    BACKUP_PREFIX,
    create_scheduled_backup,
    positive_int,
)


class ScheduledBackupTests(SimpleTestCase):
    def _database(self, path: Path, value: str = "pilot-data") -> None:
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE sample (value TEXT NOT NULL)")
            connection.execute("INSERT INTO sample (value) VALUES (?)", (value,))
            connection.commit()

    def _value(self, path: Path) -> str:
        with sqlite3.connect(path) as connection:
            return connection.execute("SELECT value FROM sample").fetchone()[0]

    def test_create_scheduled_backup_preserves_data(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.sqlite3"
            backups = root / "backups"
            self._database(source)

            created, removed = create_scheduled_backup(
                source,
                backups,
                now=datetime(2026, 11, 23, 4, 30, tzinfo=timezone.utc),
            )

            self.assertTrue(created.exists())
            self.assertEqual(removed, [])
            self.assertEqual(self._value(created), "pilot-data")
            self.assertTrue(created.name.startswith(f"{BACKUP_PREFIX}-"))

    def test_retention_prunes_only_old_worker_backups(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.sqlite3"
            backups = root / "backups"
            self._database(source)
            unrelated = backups / "keep-me.sqlite3"
            backups.mkdir()
            unrelated.write_bytes(b"unrelated")

            created = []
            for minute in (1, 2, 3):
                backup, _ = create_scheduled_backup(
                    source,
                    backups,
                    keep=2,
                    now=datetime(2026, 11, 23, 4, minute, tzinfo=timezone.utc),
                )
                created.append(backup)

            worker_backups = sorted(backups.glob(f"{BACKUP_PREFIX}-*.sqlite3"))
            self.assertEqual(worker_backups, created[1:])
            self.assertFalse(created[0].exists())
            self.assertTrue(unrelated.exists())

    def test_positive_int_falls_back_for_invalid_or_non_positive_values(self):
        self.assertEqual(positive_int("60", 10, "TEST"), 60)
        self.assertEqual(positive_int("0", 10, "TEST"), 10)
        self.assertEqual(positive_int("bad", 10, "TEST"), 10)

    def test_once_cli_creates_verified_backup(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.sqlite3"
            backups = root / "backups"
            self._database(source, "cli-data")
            script = Path(__file__).resolve().parents[1] / "scripts" / "backup_worker.py"
            env = {
                **os.environ,
                "SQLITE_DB_PATH": str(source),
                "BACKUP_DIRECTORY": str(backups),
                "BACKUP_RETENTION_COUNT": "3",
            }

            result = subprocess.run(
                [sys.executable, str(script), "--once"],
                check=False,
                capture_output=True,
                text=True,
                env=env,
                cwd=Path(__file__).resolve().parents[1],
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Scheduled backup verified:", result.stdout)
            created = list(backups.glob(f"{BACKUP_PREFIX}-*.sqlite3"))
            self.assertEqual(len(created), 1)
            self.assertEqual(self._value(created[0]), "cli-data")

    def test_once_cli_fails_when_database_is_missing(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            script = Path(__file__).resolve().parents[1] / "scripts" / "backup_worker.py"
            env = {
                **os.environ,
                "SQLITE_DB_PATH": str(root / "missing.sqlite3"),
                "BACKUP_DIRECTORY": str(root / "backups"),
            }

            result = subprocess.run(
                [sys.executable, str(script), "--once"],
                check=False,
                capture_output=True,
                text=True,
                env=env,
                cwd=Path(__file__).resolve().parents[1],
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("does not exist", result.stderr)
