from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class TvmazeFavoritePromotionContractTests(SimpleTestCase):
    def setUp(self):
        self.context_script = Path(settings.BASE_DIR, 'static', 'js', 'tmdb-context.js').read_text()
        self.watchlist_script = Path(settings.BASE_DIR, 'static', 'js', 'watchlist.js').read_text()

    def test_watchlist_exposes_existing_stable_row_reorder_helper(self):
        self.assertIn('window.aitvReorderFavoriteRow = reorderFavoriteRow', self.watchlist_script)
        self.assertIn("Number(cardIsFavorite(right)) - Number(cardIsFavorite(left))", self.watchlist_script)

    def test_resolved_existing_tvmaze_favorite_is_promoted_without_reload(self):
        self.assertIn('renderTvmazeSaveControls(card, data)', self.context_script)
        self.assertIn('if (data.favorite) window.aitvReorderFavoriteRow?.(row)', self.context_script)

    def test_promotion_is_conditioned_on_returned_favorite_state(self):
        self.assertNotIn('\n      window.aitvReorderFavoriteRow?.(row);', self.context_script)
