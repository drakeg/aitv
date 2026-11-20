from pathlib import Path

from django.test import SimpleTestCase


class LiveTvAutoRefreshScriptTests(SimpleTestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.script = (root / 'static' / 'js' / 'live-tv-auto-refresh.js').read_text()

    def test_auto_refresh_has_persistent_user_pause_control(self):
        self.assertIn("aitvLiveTvAutoRefreshPaused", self.script)
        self.assertIn("[data-live-tv-refresh-toggle]", self.script)
        self.assertIn("localStorage.getItem", self.script)
        self.assertIn("localStorage.setItem", self.script)
        self.assertIn("pausedFallback", self.script)
        self.assertIn("aria-pressed", self.script)
        self.assertIn("Pause auto-refresh", self.script)
        self.assertIn("Resume auto-refresh", self.script)

    def test_auto_refresh_still_respects_visibility_focus_and_pause(self):
        self.assertIn("readPaused() || document.visibilityState !== 'visible'", self.script)
        self.assertIn("document.activeElement", self.script)
        self.assertIn("window.location.reload()", self.script)
