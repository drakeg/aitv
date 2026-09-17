from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class LazyTmdbEnrichmentContractTests(SimpleTestCase):
    def setUp(self):
        self.script = Path(settings.BASE_DIR, 'static', 'js', 'tmdb-context.js').read_text()

    def test_tmdb_contexts_use_shared_near_viewport_observer(self):
        self.assertIn("document.querySelectorAll('[data-tmdb-context]')", self.script)
        self.assertIn('observeNearViewport(', self.script)
        self.assertIn("{rootMargin: '500px'}", self.script)

    def test_tmdb_context_is_loaded_only_once(self):
        self.assertIn("element.dataset.contextLoaded === '1'", self.script)
        self.assertIn("element.dataset.contextLoaded = '1'", self.script)

    def test_observer_fallback_preserves_older_browser_behavior(self):
        self.assertIn("if (!('IntersectionObserver' in window))", self.script)
        self.assertIn('elements.forEach(callback)', self.script)

    def test_strict_region_handling_is_preserved(self):
        self.assertIn('requireRegion && !data.is_available_in_region', self.script)
        self.assertIn("card?.classList.remove('region-pending')", self.script)
        self.assertIn('updateRowEmptyState(row)', self.script)
