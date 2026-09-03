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
        response = self.client.post(reverse('register'), {
            'username': 'newviewer',
            'password1': 'A-strong-test-password-123!',
            'password2': 'A-strong-test-password-123!',
        })
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(get_user_model().objects.filter(username='newviewer').exists())
        self.assertEqual(
            self.client.session.get('_auth_user_id'),
            str(get_user_model().objects.get(username='newviewer').pk),
        )

    def test_logout_requires_post_and_logs_user_out(self):
        user = get_user_model().objects.create_user(username='viewer', password='test-password')
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)


class DiscoverySavedStateTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='viewer', password='test-password')
        self.client.force_login(self.user)

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_live_tv_schedule', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_trending_movies')
    def test_saved_tmdb_discovery_card_is_visibly_marked(self, mock_movies, *_mocks):
        mock_movies.return_value = [{
            'id': 'tmdb_movie_42', 'title': 'Example Movie',
            'url': 'https://www.themoviedb.org/movie/42',
            'details_url': 'https://www.themoviedb.org/movie/42',
            'genre': 'Drama', 'genres': ['Drama'], 'thumbnail': '',
            'content_type': 'movie', 'description': '', 'release_year': 2026,
            'rating': 8.0, 'source_type': 'tmdb', 'external_source': 'tmdb',
            'external_id': '42', 'is_external': True,
        }]
        content = ContentItem.objects.create(
            title='Example Movie', url='https://www.themoviedb.org/movie/42',
            genre='Drama', source_type='tmdb', content_type='movie',
            external_source='tmdb', external_id='42',
        )
        Watchlist.objects.create(user=self.user, content=content)

        response = self.client.get(reverse('home'))

        self.assertContains(response, '✓ Saved to Watchlist')
        self.assertNotContains(response, '⭐ Save to Watchlist')


class LiveDashboardBrowseTests(TestCase):
    def _movie(self):
        return {
            'id': 'tmdb_movie_42', 'title': 'Galaxy Movie',
            'url': 'https://www.themoviedb.org/movie/42',
            'details_url': 'https://www.themoviedb.org/movie/42',
            'genre': 'Science Fiction, Drama', 'genres': ['Science Fiction', 'Drama'],
            'thumbnail': '', 'content_type': 'movie',
            'description': 'A journey through deep space.', 'release_year': 2026,
            'rating': 8.0, 'source_type': 'tmdb', 'external_source': 'tmdb',
            'external_id': '42', 'is_external': True,
        }

    def _tv(self):
        return {
            'id': 'tvmaze_7', 'title': 'Kitchen Stories',
            'url': 'https://www.cbs.com/shows/example/',
            'details_url': 'https://www.tvmaze.com/shows/7/example',
            'genre': 'Reality', 'genres': ['Reality'], 'thumbnail': '',
            'content_type': 'tv', 'description': 'A cooking competition.',
            'release_year': 2026, 'rating': None, 'source_type': 'tvmaze',
            'external_source': 'tvmaze', 'external_id': '7', 'is_external': True,
            'is_live_source': True, 'network': 'CBS', 'provider': 'CBS',
            'action_label': 'CBS · Sign-in required', 'episode_label': 'S1 E2',
            'runtime': 60, 'airtime': '20:00',
        }

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_trending_movies')
    @patch('core.views.fetch_live_tv_schedule')
    def test_search_uses_live_sources_not_local_catalog(self, mock_live, mock_movies, *_mocks):
        mock_live.return_value = [self._tv()]
        mock_movies.return_value = [self._movie()]
        ContentItem.objects.create(
            title='Local Sample', url='https://example.com/local', genre='Drama',
            source_type='manual', content_type='movie',
        )

        response = self.client.get(reverse('home'), {'q': 'Galaxy'})

        self.assertContains(response, 'Galaxy Movie')
        self.assertNotContains(response, 'Local Sample')
        self.assertContains(response, 'Live Search Results')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_trending_movies')
    @patch('core.views.fetch_live_tv_schedule')
    def test_type_filter_limits_live_results(self, mock_live, mock_movies, *_mocks):
        mock_live.return_value = [self._tv()]
        mock_movies.return_value = [self._movie()]

        response = self.client.get(reverse('home'), {'type': 'tv'})

        self.assertContains(response, 'Kitchen Stories')
        self.assertNotContains(response, 'Galaxy Movie')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_live_tv_schedule', return_value=[])
    def test_empty_search_has_useful_live_state(self, *_mocks):
        response = self.client.get(reverse('home'), {'q': 'definitely-not-here'})
        self.assertContains(response, 'No matching live titles found.')
        self.assertContains(response, 'Try a broader title')


class LiveSourcePresentationTests(TestCase):
    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule')
    def test_live_tv_card_shows_network_watch_action_and_detail_slots(self, mock_live, *_mocks):
        mock_live.return_value = [{
            'id': 'tvmaze_1', 'title': 'Actual Show',
            'url': 'https://www.fox.com/example/',
            'details_url': 'https://www.tvmaze.com/shows/1/example',
            'genre': 'Drama', 'genres': ['Drama'], 'thumbnail': '',
            'content_type': 'tv', 'source_type': 'tvmaze', 'external_source': 'tvmaze',
            'external_id': '1', 'is_external': True, 'is_live_source': True,
            'network': 'FOX', 'provider': 'FOX',
            'action_label': 'FOX · Sign-in required', 'release_year': 2026,
            'rating': None, 'description': '', 'episode_label': 'S1 E2',
            'runtime': 60, 'airtime': '20:00',
        }]

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'On TV Today')
        self.assertContains(response, 'Actual Show')
        self.assertContains(response, '>FOX<', html=False)
        self.assertContains(response, 'FOX · Sign-in required')
        self.assertContains(response, 'S1 E2 · 60 min · 20:00')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule', return_value=[])
    def test_dashboard_does_not_render_legacy_local_rows_or_quick_add(self, *_mocks):
        response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'Saved Network Sources')
        self.assertNotContains(response, 'Saved Movies')
        self.assertNotContains(response, 'Saved TV Shows')
        self.assertNotContains(response, 'Web Video')
        self.assertNotContains(response, 'quick-add')
