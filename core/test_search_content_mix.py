from django.test import SimpleTestCase

from content.models import DiscoveryPreference
from core.views import _ordered_live_sources


class SearchContentMixOrderingTests(SimpleTestCase):
    def setUp(self):
        self.live_tv = [{'title': 'Live TV', 'content_type': 'tv'}]
        self.trending_tv = [{'title': 'Trending TV', 'content_type': 'tv'}]
        self.on_the_air_tv = [{'title': 'On Air TV', 'content_type': 'tv'}]
        self.popular_tv = [{'title': 'Popular TV', 'content_type': 'tv'}]
        self.free_movies = [{'title': 'Free Movie', 'content_type': 'movie'}]
        self.trending_movies = [{'title': 'Trending Movie', 'content_type': 'movie'}]

    def _titles(self, content_mix):
        rows = _ordered_live_sources(
            live_tv=self.live_tv,
            trending_tv=self.trending_tv,
            on_the_air_tv=self.on_the_air_tv,
            popular_tv=self.popular_tv,
            free_movies=self.free_movies,
            trending_movies=self.trending_movies,
            content_mix=content_mix,
        )
        return [item['title'] for item in rows]

    def test_tv_first_search_sources_keep_tv_ahead_of_movies(self):
        self.assertEqual(self._titles(DiscoveryPreference.ContentMix.TV_FIRST), [
            'Live TV', 'Trending TV', 'On Air TV', 'Popular TV', 'Free Movie', 'Trending Movie',
        ])

    def test_movies_first_search_sources_keep_movies_ahead_of_tv(self):
        self.assertEqual(self._titles(DiscoveryPreference.ContentMix.MOVIES_FIRST), [
            'Free Movie', 'Trending Movie', 'Live TV', 'Trending TV', 'On Air TV', 'Popular TV',
        ])

    def test_balanced_search_sources_match_dashboard_interleaving(self):
        self.assertEqual(self._titles(DiscoveryPreference.ContentMix.BALANCED), [
            'Live TV', 'Trending TV', 'Free Movie', 'Trending Movie', 'On Air TV', 'Popular TV',
        ])
