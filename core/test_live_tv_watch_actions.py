from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse


@patch('core.views.fetch_free_archive_movies', return_value=[])
@patch('core.views.fetch_trending_movies', return_value=[])
@patch('core.views.fetch_popular_tv', return_value=[])
@patch('core.views.fetch_tv_on_the_air', return_value=[])
@patch('core.views.fetch_trending_tv', return_value=[])
class LiveTvWatchActionTests(TestCase):
    def test_schedule_card_without_official_site_does_not_invent_watch_action(self, *_mocks):
        item = {
            'id': 'tvmaze_77',
            'title': 'Network Drama',
            'url': 'https://www.tvmaze.com/shows/77/network-drama',
            'watch_url': '',
            'has_direct_watch': False,
            'details_url': 'https://www.tvmaze.com/shows/77/network-drama',
            'genre': 'Drama, Crime',
            'genres': ['Drama', 'Crime'],
            'thumbnail': '',
            'content_type': 'tv',
            'source_type': 'tvmaze',
            'description': '',
            'release_year': 2025,
            'rating': 7.8,
            'external_source': 'tvmaze',
            'external_id': '77',
            'is_external': True,
            'is_live_source': True,
            'provider': 'Example Network',
            'network': 'Example Network',
            'access_type': '',
            'action_label': '',
            'episode_label': 'S2 E4',
            'airtime': '21:00',
            'runtime': 44,
            'show_type': 'Scripted',
            'is_news': False,
        }

        with patch('core.views.fetch_live_tv_schedule', return_value=[item]):
            response = self.client.get(reverse('home'))

        self.assertContains(response, 'Network Drama')
        self.assertContains(response, 'Example Network')
        self.assertContains(response, 'S2 E4 · 44 min · 21:00')
        self.assertContains(response, 'Direct watch link not listed by source')
        self.assertContains(response, 'Source details')
        self.assertNotContains(response, 'Watch on Example Network')
