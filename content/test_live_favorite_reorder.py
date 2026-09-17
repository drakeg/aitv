from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class LiveFavoriteReorderContractTests(SimpleTestCase):
    def setUp(self):
        self.script = Path(settings.BASE_DIR, 'static', 'js', 'watchlist.js').read_text()

    def test_favorite_updates_synchronize_duplicate_cards(self):
        self.assertIn("document.querySelectorAll('[data-favorite-form]')", self.script)
        self.assertIn('form.action === action', self.script)
        self.assertIn('synchronizeFavoriteState(favoriteForm.action, result.favorite)', self.script)

    def test_discovery_rows_are_reordered_after_favorite_changes(self):
        self.assertIn('function reorderFavoriteRow(row)', self.script)
        self.assertIn("child.classList.contains('card')", self.script)
        self.assertIn('Number(cardIsFavorite(right)) - Number(cardIsFavorite(left))', self.script)
        self.assertIn("form.closest('[data-discovery-row]')", self.script)

    def test_watchlist_removal_reorders_card_out_of_favorite_group(self):
        self.assertIn("favorite.remove()", self.script)
        self.assertIn("reorderFavoriteRow(container.closest('[data-discovery-row]'))", self.script)

    def test_asset_version_is_refreshed(self):
        base = Path(settings.BASE_DIR, 'templates', 'base.html').read_text()
        self.assertIn("watchlist.js' %}?v=5", base)
