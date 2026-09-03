import os
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from content.services import fetch_tmdb_watch_context


class TmdbWatchContextServiceTests(SimpleTestCase):
    @patch.dict(os.environ, {'TMDB_API_KEY': 'test-key'}, clear=True)
    @patch('content.services.requests.get')
    def test_tv_context_includes_network_episode_runtime_and_us_providers(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            'networks': [{'name': 'FX'}],
            'last_episode_to_air': {'season_number': 3, 'episode_number': 7, 'runtime': 52},
            'watch/providers': {'results': {'US': {
                'link': 'https://www.themoviedb.org/tv/42/watch',
                'flatrate': [{'provider_name': 'Hulu'}],
                'ads': [{'provider_name': 'Tubi'}],
            }}},
        }
        mock_get.return_value = response

        context = fetch_tmdb_watch_context('tv', '42', region='US')

        self.assertEqual(context['region'], 'US')
        self.assertTrue(context['is_available_in_region'])
        self.assertEqual(context['network'], 'FX')
        self.assertEqual(context['episode_label'], 'S3 E7')
        self.assertEqual(context['runtime'], 52)
        self.assertEqual(context['providers'][0], {'name': 'Tubi', 'access': 'Free with ads'})
        self.assertIn({'name': 'Hulu', 'access': 'Subscription'}, context['providers'])

    @patch.dict(os.environ, {'TMDB_API_KEY': 'test-key'}, clear=True)
    @patch('content.services.requests.get')
    def test_region_without_provider_is_marked_unavailable(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            'runtime': 118,
            'watch/providers': {'results': {
                'CA': {'link': 'https://www.themoviedb.org/movie/9/watch', 'free': [{'provider_name': 'Plex'}]},
            }},
        }
        mock_get.return_value = response

        context = fetch_tmdb_watch_context('movie', '9', region='US')

        self.assertEqual(context['region'], 'US')
        self.assertFalse(context['is_available_in_region'])
        self.assertEqual(context['providers'], [])
        self.assertEqual(context['watch_url'], '')


class TmdbWatchContextViewTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch('content.views.fetch_tmdb_watch_context')
    def test_context_endpoint_caches_per_region(self, mock_fetch):
        mock_fetch.return_value = {
            'region': 'US',
            'network': 'FX',
            'networks': ['FX'],
            'runtime': 52,
            'episode_label': 'S3 E7',
            'providers': [{'name': 'Hulu', 'access': 'Subscription'}],
            'watch_url': 'https://www.themoviedb.org/tv/42/watch',
            'is_available_in_region': True,
        }
        url = reverse('content:tmdb_watch_context', args=['tv', 42])

        first = self.client.get(url, {'region': 'US'})
        second = self.client.get(url, {'region': 'US'})

        self.assertEqual(first.status_code, 200)
        self.assertJSONEqual(first.content, mock_fetch.return_value)
        self.assertEqual(second.status_code, 200)
        mock_fetch.assert_called_once_with('tv', 42, region='US')
