import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("badges", Path(__file__).resolve().parents[1] / "scripts" / "badges.py")
badges = importlib.util.module_from_spec(spec)
spec.loader.exec_module(badges)

class BadgeTests(unittest.TestCase):
    def test_idempotent_preserves_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Example\n\nProject details.\n", encoding="utf-8")
            (root / "pyproject.toml").write_text("[project]\nname='example'\n", encoding="utf-8")
            self.assertTrue(badges.apply(root, write=True)[0])
            first = (root / "README.md").read_text()
            self.assertFalse(badges.apply(root, write=True)[0])
            self.assertEqual(first, (root / "README.md").read_text())
            self.assertIn("Project details.", first)
            self.assertIn("Python", first)
    def test_malformed_markers_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Test\n" + badges.START)
            with self.assertRaises(ValueError): badges.apply(root, write=True)

    def test_verified_versions_and_sqlite_are_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Test\n", encoding="utf-8")
            (root / "requirements.txt").write_text("Django==6.1.3\n", encoding="utf-8")
            (root / "Dockerfile").write_text("FROM python:3.15-slim\n", encoding="utf-8")
            (root / "project").mkdir()
            (root / "project" / "settings.py").write_text(
                "DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3'}}\n",
                encoding="utf-8",
            )
            generated = badges.generate(root)
            self.assertIn("Django%206.1.3", generated)
            self.assertIn("Python%203.15", generated)
            self.assertIn("SQLite", generated)
            self.assertIn("https://www.sqlite.org/", generated)
            self.assertIn("https://www.djangoproject.com/", generated)

    def test_versions_are_not_claimed_without_exact_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Test\n", encoding="utf-8")
            (root / "requirements.txt").write_text("Django>=6\n", encoding="utf-8")
            generated = badges.generate(root)
            self.assertIn("Django", generated)
            self.assertNotIn("Django%206", generated)

    def test_unverified_tech_not_claimed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Test\n\nReact is cool.")
            self.assertNotIn("React", badges.generate(root))
if __name__ == "__main__": unittest.main()
