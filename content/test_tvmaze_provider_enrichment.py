from unittest.mock import Mock, patch

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from content.services import fetch_tv_watch_options_by_title


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
        mock_fetch.assert_called_once_with('Example Show', region='US', release_year=2025)

    def test_watch_options_endpoint_rejects_blank_title(self):
        response = self.client.get(reverse('content:tvmaze_watch_options'), {'region': 'US'})
        self.assertEqual(response.status_code, 400)
