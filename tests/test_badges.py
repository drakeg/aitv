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
    def test_unverified_tech_not_claimed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Test\n\nReact is cool.")
            self.assertNotIn("React", badges.generate(root))
if __name__ == "__main__": unittest.main()
