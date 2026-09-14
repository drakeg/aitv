import warnings
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.cache import CacheKeyWarning, cache
from django.test import TestCase
from django.urls import reverse

from content.models import ContentItem
from content.services import fetch_tv_watch_options_by_title
from watchlist.models import Watchlist


class TVMazeProviderEnrichmentServiceTests(TestCase):
    @patch('content.services.fetch_tmdb_watch_context')
    @patch('content.services.requests.get')
    @patch.dict('os.environ', {'TMDB_API_KEY': 'test-key'})
    def test_exact_title_match_resolves_regional_watch_context(self, mock_get, mock_context):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            'results': [
                {'id': 10, 'name': 'Similar Show', 'first_air_date': '2026-01-01'},
                {'id': 20, 'name': 'Example Show', 'first_air_date': '2025-09-01'},
            ]
        }
        mock_get.return_value = response
        mock_context.return_value = {
            'region': 'US',
            'providers': [{'name': 'Example+', 'access': 'Subscription'}],
            'provider_count': 1,
            'additional_provider_count': 0,
            'watch_url': 'https://example.test/watch-options',
            'is_available_in_region': True,
        }

        result = fetch_tv_watch_options_by_title('Example Show', region='US', release_year=2025)

        self.assertTrue(result['matched'])
        self.assertEqual(result['tmdb_id'], '20')
        self.assertEqual(result['providers'][0]['name'], 'Example+')
        mock_context.assert_called_once_with('tv', 20, region='US')

    @patch('content.services.fetch_tmdb_watch_context')
    @patch('content.services.requests.get')
    @patch.dict('os.environ', {'TMDB_API_KEY': 'test-key'})
    def test_non_exact_title_is_not_guessed(self, mock_get, mock_context):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {'results': [{'id': 10, 'name': 'Example Show UK'}]}
        mock_get.return_value = response

        self.assertEqual(fetch_tv_watch_options_by_title('Example Show', region='US'), {})
        mock_context.assert_not_called()


class TVMazeProviderEnrichmentViewTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch('content.views.fetch_tv_watch_options_by_title')
    def test_watch_options_endpoint_caches_result(self, mock_fetch):
        mock_fetch.return_value = {
            'matched': True,
            'tmdb_id': '20',
            'region': 'US',
            'providers': [{'name': 'Example+', 'access': 'Subscription'}],
            'is_available_in_region': True,
        }
        url = reverse('content:tvmaze_watch_options')

        first = self.client.get(url, {'title': 'Example Show', 'region': 'US', 'year': '2025'})
        second = self.client.get(url, {'title': 'Example Show', 'region': 'US', 'year': '2025'})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()['providers'][0]['name'], 'Example+')
        self.assertFalse(first.json()['saved'])
        mock_fetch.assert_called_once_with('Example Show', region='US', release_year=2025)

    @patch('content.views.fetch_tv_watch_options_by_title')
    def test_watch_options_cache_key_is_safe_for_spaces_and_special_characters(self, mock_fetch):
        mock_fetch.return_value = {
            'matched': True,
            'tmdb_id': '21',
            'region': 'US',
            'providers': [],
            'is_available_in_region': False,
        }
        url = reverse('content:tvmaze_watch_options')
        title = 'Law & Order: Special Victims Unit / 2026?'

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', CacheKeyWarning)
            first = self.client.get(url, {'title': title, 'region': 'US', 'year': '2026'})
            second = self.client.get(url, {'title': title, 'region': 'US', 'year': '2026'})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertFalse(any(issubclass(warning.category, CacheKeyWarning) for warning in caught))
        mock_fetch.assert_called_once_with(title, region='US', release_year=2026)

    @patch('content.views.fetch_tv_watch_options_by_title')
    def test_watch_options_adds_current_users_saved_favorite_state_after_cache_lookup(self, mock_fetch):
        mock_fetch.return_value = {
            'matched': True,
            'tmdb_id': '20',
            'tmdb_title': 'Example Show',
            'tmdb_details_url': 'https://www.themoviedb.org/tv/20',
            'region': 'US',
            'providers': [{'name': 'Example+', 'access': 'Subscription'}],
            'is_available_in_region': True,
        }
        user = get_user_model().objects.create_user(username='tvmaze-saver', password='test-password')
        item = ContentItem.objects.create(
            title='Example Show',
            url='https://www.themoviedb.org/tv/20',
            genre='Drama',
            source_type='tmdb',
            content_type='tv',
            external_source='tmdb',
            external_id='20',
        )
        Watchlist.objects.create(user=user, content=item, is_favorite=True)
        url = reverse('content:tvmaze_watch_options')

        self.client.force_login(user)
        saved = self.client.get(url, {'title': 'Example Show', 'region': 'US', 'year': '2025'})
        self.client.logout()
        anonymous = self.client.get(url, {'title': 'Example Show', 'region': 'US', 'year': '2025'})

        self.assertTrue(saved.json()['saved'])
        self.assertTrue(saved.json()['favorite'])
        self.assertEqual(saved.json()['content_id'], item.id)
        self.assertEqual(saved.json()['remove_url'], reverse('watchlist:remove', args=[item.id]))
        self.assertEqual(saved.json()['favorite_url'], reverse('watchlist:favorite', args=[item.id]))
        self.assertFalse(anonymous.json()['saved'])
        self.assertFalse(anonymous.json()['favorite'])
        mock_fetch.assert_called_once_with('Example Show', region='US', release_year=2025)

    def test_watch_options_endpoint_rejects_blank_title(self):
        response = self.client.get(reverse('content:tvmaze_watch_options'), {'region': 'US'})
        self.assertEqual(response.status_code, 400)
