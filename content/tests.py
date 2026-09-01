import os
from unittest.mock import Mock, patch

import requests
from django.test import SimpleTestCase

from content.services import fetch_trending_movies


class TrendingMoviesServiceTests(SimpleTestCase):
    @patch.dict(os.environ, {}, clear=True)
    @patch('content.services.requests.get')
    def test_missing_api_key_skips_request(self, mock_get):
        self.assertEqual(fetch_trending_movies(), [])
        mock_get.assert_not_called()

    @patch.dict(
        os.environ,
        {'TMDB_API_KEY': 'test-key', 'TMDB_TIMEOUT_SECONDS': '3'},
        clear=True,
    )
    @patch('content.services.requests.get')
    def test_trending_movies_are_normalized(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            'results': [
                {
                    'id': 42,
                    'title': 'Example Movie',
                    'poster_path': '/poster.jpg',
                }
            ]
        }
        mock_get.return_value = response

        movies = fetch_trending_movies()

        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]['id'], 'tmdb_42')
        self.assertEqual(movies[0]['title'], 'Example Movie')
        self.assertTrue(movies[0]['is_external'])
        mock_get.assert_called_once_with(
            'https://api.themoviedb.org/3/trending/movie/week',
            params={'api_key': 'test-key'},
            timeout=3.0,
        )

    @patch.dict(os.environ, {'TMDB_API_KEY': 'test-key'}, clear=True)
    @patch('content.services.requests.get')
    def test_request_failure_returns_empty_list(self, mock_get):
        mock_get.side_effect = requests.RequestException('unavailable')

        self.assertEqual(fetch_trending_movies(), [])

    @patch.dict(
        os.environ,
        {'TMDB_API_KEY': 'test-key', 'TMDB_TIMEOUT_SECONDS': 'invalid'},
        clear=True,
    )
    def test_invalid_timeout_returns_empty_list(self):
        self.assertEqual(fetch_trending_movies(), [])
