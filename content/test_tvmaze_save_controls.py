from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class TVMazeSaveControlsContractTests(SimpleTestCase):
    def setUp(self):
        self.script = Path(settings.BASE_DIR, 'static', 'js', 'tmdb-context.js').read_text()
        self.home_template = Path(settings.BASE_DIR, 'templates', 'home.html').read_text()

    def test_all_tvmaze_cards_participate_in_lazy_identity_resolution(self):
        self.assertIn("document.querySelectorAll('.card[data-source-type=\"tvmaze\"]')", self.script)
        self.assertIn('observeNearViewport(tvmazeCards', self.script)

    def test_authenticated_discovery_exposes_existing_watchlist_workflow(self):
        self.assertIn('data-authenticated=', self.home_template)
        self.assertIn('data-import-url=', self.home_template)
        self.assertIn("form.dataset.watchlistForm = ''", self.script)
        self.assertIn("form.dataset.externalSave = 'true'", self.script)
        self.assertIn("appendHidden(form, 'external_source', 'tmdb')", self.script)
        self.assertIn("appendHidden(form, 'external_id', data.tmdb_id)", self.script)

    def test_existing_saved_and_favorite_state_is_rendered(self):
        self.assertIn('data.saved && data.remove_url', self.script)
        self.assertIn('data.favorite_url', self.script)
        self.assertIn("favorite.dataset.favoriteState = data.favorite ? '1' : '0'", self.script)

    def test_direct_network_watch_action_is_not_replaced(self):
        self.assertIn("const metadataOnly = card.dataset.hasDirectWatch === '0'", self.script)
        self.assertIn('if (metadataOnly && data.is_available_in_region && providerBox)', self.script)
