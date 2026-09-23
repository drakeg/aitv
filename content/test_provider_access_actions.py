from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class ProviderAccessActionContractTests(SimpleTestCase):
    def setUp(self):
        self.script = (Path(settings.BASE_DIR) / 'static' / 'js' / 'tmdb-context.js').read_text()

    def test_free_access_is_preferred_in_primary_watch_copy(self):
        self.assertIn("if (bestAccess === 'Free') return 'Find free watch option';", self.script)
        self.assertIn("if (bestAccess === 'Free with ads') return 'Find free-with-ads option';", self.script)

    def test_paid_access_labels_remain_explicit(self):
        self.assertIn("if (bestAccess === 'Subscription') return 'Find subscription option';", self.script)
        self.assertIn("if (bestAccess === 'Rent') return 'Find rental option';", self.script)
        self.assertIn("if (bestAccess === 'Buy') return 'Find purchase option';", self.script)

    def test_tmdb_and_tvmaze_regional_actions_share_access_labeling(self):
        self.assertIn('watch.textContent = watchActionLabel(data);', self.script)
        self.assertIn('action.textContent = watchActionLabel(data);', self.script)

    def test_no_provider_specific_url_is_fabricated(self):
        self.assertNotIn('provider.url', self.script)
        self.assertIn("return 'Open provider listing';", self.script)
