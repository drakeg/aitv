from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from content.models import ContentItem
from watchlist.models import Watchlist


@patch('core.views.fetch_free_archive_movies', return_value=[])
@patch('core.views.fetch_trending_movies', return_value=[])
@patch('core.views.fetch_popular_tv', return_value=[])
@patch('core.views.fetch_tv_on_the_air', return_value=[])
@patch('core.views.fetch_live_tv_schedule', return_value=[])
class DiscoveryFavoriteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='favorite-viewer', password='test-password')

    def _tmdb_tv(self):
        return {
            'id': 'tmdb_tv_7',
            'title': 'Favorite Series',
            'url': 'https://www.themoviedb.org/tv/7',
            'details_url': 'https://www.themoviedb.org/tv/7',
            'genre': 'Drama',
            'genres': ['Drama'],
            'thumbnail': '',
            'content_type': 'tv',
            'description': '',
            'release_year': 2026,
            'rating': 8.0,
            'source_type': 'tmdb',
            'external_source': 'tmdb',
            'external_id': '7',
            'is_external': True,
            'is_news': False,
        }

    @patch('core.views.fetch_trending_tv')
    def test_saved_favorite_is_rendered_on_discovery_card(self, mock_trending, *_mocks):
        mock_trending.return_value = [self._tmdb_tv()]
        item = ContentItem.objects.create(
            title='Favorite Series',
            url='https://www.themoviedb.org/tv/7',
            genre='Drama',
            content_type='tv',
            source_type='tmdb',
            external_source='tmdb',
            external_id='7',
        )
        Watchlist.objects.create(user=self.user, content=item, is_favorite=True)
        self.client.force_login(self.user)

        response = self.client.get(reverse('home'))

        self.assertContains(response, '★ Favorite')
        self.assertContains(response, reverse('watchlist:favorite', args=[item.id]))
        self.assertContains(response, 'data-favorite-state="1"', html=False)

    @patch('core.views.fetch_trending_tv', return_value=[])
    def test_external_async_save_returns_favorite_action(self, _mock_trending, *_mocks):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('content:import_external'),
            {
                'title': 'New Series',
                'url': 'https://www.themoviedb.org/tv/8',
                'genre': 'Drama',
                'content_type': 'tv',
                'external_source': 'tmdb',
                'external_id': '8',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['saved'])
        self.assertFalse(payload['favorite'])
        self.assertEqual(payload['favorite_url'], reverse('watchlist:favorite', args=[payload['content_id']]))
