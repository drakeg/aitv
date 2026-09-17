from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class ProviderPreferenceMigrationContractTests(SimpleTestCase):
    def test_provider_preference_migration_exists(self):
        migration = Path(settings.BASE_DIR, 'content', 'migrations', '0010_discoverypreference_preferred_providers.py').read_text()
        self.assertIn("name='preferred_providers'", migration)
        self.assertIn('models.JSONField(blank=True, default=list)', migration)
