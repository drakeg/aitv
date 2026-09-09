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
        self.user = get_user_model().objects.create_user(username='viewer', password='test-password')
        self.tmdb = {
            'id': 'tmdb_tv_7', 'title': 'Example Series',
            'url': 'https://www.themoviedb.org/tv/7',
            'details_url': 'https://www.themoviedb.org/tv/7',
            'genre': 'Drama', 'genres': ['Drama'], 'thumbnail': '', 'content_type': 'tv',
            'description': '', 'release_year': 2026, 'rating': 8.0, 'source_type': 'tmdb',
            'external_source': 'tmdb', 'external_id': '7', 'is_external': True, 'is_news': False,
        }

    @patch('core.views.fetch_trending_tv')
    def test_saved_tmdb_card_shows_favorite_control(self, mock_trending, *_mocks):
        mock_trending.return_value = [self.tmdb]
        item = ContentItem.objects.create(
            title='Example Series', url='https://www.themoviedb.org/tv/7', genre='Drama',
            source_type='tmdb', content_type='tv', external_source='tmdb', external_id='7',
        )
        Watchlist.objects.create(user=self.user, content=item, is_favorite=False)
        self.client.force_login(self.user)

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'data-favorite-form', html=False)
        self.assertContains(response, '☆ Mark favorite')
        self.assertContains(response, reverse('watchlist:favorite', args=[item.id]))

    @patch('core.views.fetch_trending_tv')
    def test_favorite_tmdb_card_renders_active_state(self, mock_trending, *_mocks):
        mock_trending.return_value = [self.tmdb]
        item = ContentItem.objects.create(
            title='Example Series', url='https://www.themoviedb.org/tv/7', genre='Drama',
            source_type='tmdb', content_type='tv', external_source='tmdb', external_id='7',
        )
        Watchlist.objects.create(user=self.user, content=item, is_favorite=True)
        self.client.force_login(self.user)

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'data-favorite-state="1"', html=False)
        self.assertContains(response, '★ Favorite')

    @patch('core.views.fetch_trending_tv')
    def test_unsaved_tmdb_card_does_not_show_favorite_until_saved(self, mock_trending, *_mocks):
        mock_trending.return_value = [self.tmdb]
        self.client.force_login(self.user)

        response = self.client.get(reverse('home'))

        self.assertNotContains(response, 'data-favorite-form', html=False)
        self.assertContains(response, '⭐ Save to Watchlist')
