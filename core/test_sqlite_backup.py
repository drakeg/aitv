import sqlite3
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from scripts.sqlite_backup import (
    BackupError,
    create_backup,
    restore_backup,
    verify_database,
)


class SQLiteBackupTests(SimpleTestCase):
    def _database(self, path: Path, value: str) -> None:
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE sample (value TEXT NOT NULL)")
            connection.execute("INSERT INTO sample (value) VALUES (?)", (value,))
            connection.commit()

    def _value(self, path: Path) -> str:
        with sqlite3.connect(path) as connection:
            return connection.execute("SELECT value FROM sample").fetchone()[0]

    def test_create_backup_preserves_data_and_passes_integrity_check(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.sqlite3"
            backup = root / "backup.sqlite3"
            self._database(source, "pilot-data")

            created = create_backup(source, backup)

            self.assertEqual(created, backup.resolve())
            self.assertEqual(verify_database(backup), backup.resolve())
            self.assertEqual(self._value(backup), "pilot-data")

    def test_verify_database_rejects_corrupt_input(self):
        with TemporaryDirectory() as directory:
            corrupt = Path(directory) / "corrupt.sqlite3"
            corrupt.write_bytes(b"not a sqlite database")

            with self.assertRaises(BackupError):
                verify_database(corrupt)

    def test_backup_refuses_to_overwrite_source_path(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "source.sqlite3"
            self._database(database, "original")

            with self.assertRaisesRegex(BackupError, "destination must differ"):
                create_backup(database, database)

    def test_restore_requires_explicit_offline_confirmation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.sqlite3"
            target = root / "target.sqlite3"
            self._database(source, "backup")
            self._database(target, "current")

            with self.assertRaisesRegex(BackupError, "confirm-offline"):
                restore_backup(source, target)

            self.assertEqual(self._value(target), "current")

    def test_restore_replaces_target_and_keeps_pre_restore_safety_backup(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            backup = root / "backup.sqlite3"
            target = root / "target.sqlite3"
            self._database(backup, "restored")
            self._database(target, "before-restore")

            restored, safety_backup = restore_backup(
                backup,
                target,
                confirm_offline=True,
            )

            self.assertEqual(restored, target.resolve())
            self.assertIsNotNone(safety_backup)
            self.assertTrue(safety_backup.exists())
            self.assertEqual(self._value(target), "restored")
            self.assertEqual(self._value(safety_backup), "before-restore")

    def test_restore_refuses_same_source_and_target(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "database.sqlite3"
            self._database(database, "same")

            with self.assertRaisesRegex(BackupError, "source must differ"):
                restore_backup(
                    database,
                    database,
                    confirm_offline=True,
                )

    def test_cli_backup_verify_and_restore_round_trip(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.sqlite3"
            backup = root / "backup.sqlite3"
            target = root / "target.sqlite3"
            self._database(source, "cli-backup")
            self._database(target, "old-target")
            script = Path(__file__).resolve().parents[1] / "scripts" / "sqlite_backup.py"

            backup_result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "backup",
                    "--source",
                    str(source),
                    "--output",
                    str(backup),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(backup_result.returncode, 0, backup_result.stderr)
            self.assertIn("Backup verified:", backup_result.stdout)

            verify_result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "verify",
                    "--input",
                    str(backup),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(verify_result.returncode, 0, verify_result.stderr)

            restore_result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "restore",
                    "--input",
                    str(backup),
                    "--target",
                    str(target),
                    "--confirm-offline",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(restore_result.returncode, 0, restore_result.stderr)
            self.assertIn("Restore verified:", restore_result.stdout)
            self.assertIn("Pre-restore safety backup:", restore_result.stdout)
            self.assertEqual(self._value(target), "cli-backup")
