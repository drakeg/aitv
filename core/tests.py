from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from content.models import ContentItem
from watchlist.models import Watchlist


class AuthenticationFlowTests(TestCase):
    def test_login_page_is_available(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in')

    def test_registration_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newviewer',
                'password1': 'A-strong-test-password-123!',
                'password2': 'A-strong-test-password-123!',
            },
        )

        self.assertRedirects(response, reverse('home'))
        self.assertTrue(get_user_model().objects.filter(username='newviewer').exists())
        self.assertEqual(self.client.session.get('_auth_user_id'), str(get_user_model().objects.get(username='newviewer').pk))

    def test_logout_requires_post_and_logs_user_out(self):
        user = get_user_model().objects.create_user(username='viewer', password='test-password')
        self.client.force_login(user)

        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)


class DiscoverySavedStateTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='viewer',
            password='test-password',
        )
        self.client.force_login(self.user)

    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_trending_movies')
    def test_saved_tmdb_discovery_card_is_visibly_marked(self, mock_movies, _mock_tv):
        mock_movies.return_value = [{
            'id': 'tmdb_movie_42',
            'title': 'Example Movie',
            'url': 'https://www.themoviedb.org/movie/42',
            'genre': 'Movie',
            'thumbnail': '',
            'content_type': 'movie',
            'description': '',
            'release_year': 2026,
            'rating': 8.0,
            'source_type': 'tmdb',
            'external_source': 'tmdb',
            'external_id': '42',
            'is_external': True,
        }]
        content = ContentItem.objects.create(
            title='Example Movie',
            url='https://www.themoviedb.org/movie/42',
            genre='Movie',
            source_type='tmdb',
            content_type='movie',
            external_source='tmdb',
            external_id='42',
        )
        Watchlist.objects.create(user=self.user, content=content)

        response = self.client.get(reverse('home'))

        self.assertContains(response, '✓ Saved to Watchlist')
        self.assertNotContains(response, '⭐ Save to Watchlist')
