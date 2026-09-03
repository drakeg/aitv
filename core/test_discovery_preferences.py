from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


class DiscoveryPreferenceTests(TestCase):
    def _item(self, title, genres, *, is_news=False):
        return {
            'id': title.lower().replace(' ', '-'),
            'title': title,
            'url': 'https://example.com/watch',
            'details_url': '',
            'genre': ', '.join(genres),
            'genres': genres,
            'thumbnail': '',
            'content_type': 'tv',
            'source_type': 'tvmaze',
            'description': '',
            'release_year': 2026,
            'rating': None,
            'external_source': 'tvmaze',
            'external_id': title,
            'is_external': True,
            'is_live_source': True,
            'provider': 'Example Network',
            'network': 'Example Network',
            'access_type': 'other',
            'action_label': 'Watch on Example Network',
            'episode_label': 'S1 E1',
            'airtime': '20:00',
            'runtime': 60,
            'is_news': is_news,
        }

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule')
    def test_news_is_hidden_by_default(self, mock_live, *_mocks):
        mock_live.return_value = [
            self._item('Evening News', ['News'], is_news=True),
            self._item('Funny Show', ['Comedy']),
        ]
        response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'Evening News')
        self.assertContains(response, 'Funny Show')
        self.assertContains(response, 'News is hidden by default.')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule')
    def test_news_can_be_explicitly_included(self, mock_live, *_mocks):
        mock_live.return_value = [self._item('Evening News', ['News'], is_news=True)]
        response = self.client.get(reverse('home'), {'include_news': '1'})
        self.assertContains(response, 'Evening News')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule')
    def test_genre_filter_focuses_live_discovery(self, mock_live, *_mocks):
        mock_live.return_value = [
            self._item('Funny Show', ['Comedy']),
            self._item('Police Drama', ['Crime', 'Drama']),
        ]
        response = self.client.get(reverse('home'), {'genre': 'Crime'})
        self.assertContains(response, 'Police Drama')
        self.assertNotContains(response, 'Funny Show')
        self.assertContains(response, 'On TV Today · Crime')
