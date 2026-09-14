from pathlib import Path

from django.test import SimpleTestCase


class NotificationWorkerComposeTests(SimpleTestCase):
    def test_notifications_profile_runs_release_checker_on_interval(self):
        compose = (Path(__file__).resolve().parents[1] / 'docker-compose.yml').read_text()

        self.assertIn('notifications:', compose)
        self.assertIn('profiles:', compose)
        self.assertIn('- notifications', compose)
        self.assertIn('python manage.py check_release_notifications', compose)
        self.assertIn('RELEASE_CHECK_INTERVAL_SECONDS', compose)
        self.assertIn('until [ -f /data/db.sqlite3 ]', compose)
        self.assertIn('- aitv_data:/data', compose)

    def test_default_interval_is_documented(self):
        env_example = (Path(__file__).resolve().parents[1] / '.env.example').read_text()
        self.assertIn('RELEASE_CHECK_INTERVAL_SECONDS=3600', env_example)
