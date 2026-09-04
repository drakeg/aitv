from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class TVDiscoveryDepthTests(TestCase):
    def _tv(self, external_id, title):
        return {
            'id': f'tmdb_tv_{external_id}',
            'title': title,
            'url': f'https://www.themoviedb.org/tv/{external_id}',
            'details_url': f'https://www.themoviedb.org/tv/{external_id}',
            'genre': 'Drama',
            'genres': ['Drama'],
            'thumbnail': '',
            'content_type': 'tv',
            'description': '',
            'release_year': 2026,
            'rating': 8.0,
            'source_type': 'tmdb',
            'external_source': 'tmdb',
            'external_id': str(external_id),
            'is_external': True,
            'is_news': False,
        }

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_popular_tv')
    @patch('core.views.fetch_tv_on_the_air')
    @patch('core.views.fetch_trending_tv')
    @patch('core.views.fetch_live_tv_schedule', return_value=[])
    def test_tv_rows_are_deep_and_deduplicated(
        self,
        _mock_live,
        mock_trending,
        mock_on_air,
        mock_popular,
        *_mocks,
    ):
        shared = self._tv(1, 'Shared Series')
        mock_trending.return_value = [shared, self._tv(2, 'Daily Trend')]
        mock_on_air.return_value = [shared, self._tv(3, 'On Air Series')]
        mock_popular.return_value = [self._tv(3, 'On Air Series'), self._tv(4, 'Popular Series')]

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Trending TV Today')
        self.assertContains(response, 'TV On the Air')
        self.assertContains(response, 'Popular TV')
        self.assertEqual(response.content.decode().count('Shared Series'), 1)
        self.assertEqual(response.content.decode().count('On Air Series'), 1)
        self.assertContains(response, 'Popular Series')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_popular_tv', return_value=[])
    @patch('core.views.fetch_tv_on_the_air', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule', return_value=[])
    def test_live_schedule_requests_larger_pool(self, mock_live, *_mocks):
        self.client.get(reverse('home'))
        mock_live.assert_called_once_with(limit=100, country='US')
