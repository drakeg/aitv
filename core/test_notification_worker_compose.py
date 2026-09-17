from pathlib import Path

from django.test import SimpleTestCase


class NotificationWorkerComposeTests(SimpleTestCase):
    def setUp(self):
        self.compose = (Path(__file__).resolve().parents[1] / 'docker-compose.yml').read_text()

    def test_notifications_profile_runs_release_checker_on_interval(self):
        self.assertIn('notifications:', self.compose)
        self.assertIn('profiles:', self.compose)
        self.assertIn('- notifications', self.compose)
        self.assertIn('python manage.py check_release_notifications', self.compose)
        self.assertIn('RELEASE_CHECK_INTERVAL_SECONDS', self.compose)
        self.assertIn('until [ -f /data/db.sqlite3 ]', self.compose)
        self.assertIn('- aitv_data:/data', self.compose)

    def test_worker_recovers_from_failed_release_check(self):
        self.assertIn('if ! python manage.py check_release_notifications; then', self.compose)
        self.assertIn('Favorite release check failed; retrying after $$interval seconds.', self.compose)
        self.assertIn('restart: unless-stopped', self.compose)

    def test_worker_rejects_invalid_or_zero_intervals(self):
        self.assertIn('*[!0-9]*', self.compose)
        self.assertIn('0) echo "RELEASE_CHECK_INTERVAL_SECONDS must be greater than zero;', self.compose)
        self.assertIn('interval=3600', self.compose)
        self.assertIn('sleep "$$interval"', self.compose)

    def test_default_interval_is_documented(self):
        env_example = (Path(__file__).resolve().parents[1] / '.env.example').read_text()
        self.assertIn('RELEASE_CHECK_INTERVAL_SECONDS=3600', env_example)
