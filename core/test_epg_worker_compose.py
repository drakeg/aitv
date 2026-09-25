from pathlib import Path

from django.test import SimpleTestCase


class EpgWorkerComposeTests(SimpleTestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.compose = (root / 'docker-compose.yml').read_text()
        self.env_example = (root / '.env.example').read_text()

    def test_epg_profile_runs_refresh_command_on_interval(self):
        self.assertIn('  epg:', self.compose)
        self.assertIn('- epg', self.compose)
        self.assertIn('python manage.py refresh_epg --regions "$$regions" --retention-hours "$$retention"', self.compose)
        self.assertIn('EPG_REFRESH_INTERVAL_SECONDS', self.compose)
        self.assertIn('EPG_REGIONS', self.compose)
        self.assertIn('EPG_RETENTION_HOURS', self.compose)
        self.assertIn('until [ -f /data/db.sqlite3 ]', self.compose)
        self.assertIn('- aitv_data:/data', self.compose)

    def test_epg_worker_recovers_from_failed_refresh(self):
        self.assertIn('if ! python manage.py refresh_epg', self.compose)
        self.assertIn('EPG refresh failed; retrying after $$interval seconds.', self.compose)
        self.assertIn('restart: unless-stopped', self.compose)

    def test_epg_worker_rejects_invalid_or_zero_interval(self):
        self.assertIn('EPG_REFRESH_INTERVAL_SECONDS must be a positive integer; using 1800.', self.compose)
        self.assertIn('EPG_REFRESH_INTERVAL_SECONDS must be greater than zero; using 1800.', self.compose)
        self.assertIn('interval=1800', self.compose)
        self.assertIn('sleep "$$interval"', self.compose)

    def test_epg_defaults_are_documented(self):
        self.assertIn('EPG_REGIONS=US', self.env_example)
        self.assertIn('EPG_REFRESH_INTERVAL_SECONDS=1800', self.env_example)
        self.assertIn('EPG_RETENTION_HOURS=6', self.env_example)
