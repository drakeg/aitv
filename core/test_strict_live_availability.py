from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from content.models import DiscoveryPreference


@patch('core.views.fetch_free_archive_movies', return_value=[])
@patch('core.views.fetch_trending_movies', return_value=[])
@patch('core.views.fetch_popular_tv', return_value=[])
@patch('core.views.fetch_tv_on_the_air', return_value=[])
@patch('core.views.fetch_trending_tv', return_value=[])
class StrictLiveAvailabilityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='strict-viewer', password='test-password')

    def _live_item(self, title, *, has_direct_watch):
        return {
            'id': title.lower().replace(' ', '-'),
            'title': title,
            'url': 'https://example.com/watch' if has_direct_watch else '',
            'details_url': 'https://www.tvmaze.com/shows/1/example',
            'genre': 'Drama',
            'genres': ['Drama'],
            'thumbnail': '',
            'content_type': 'tv',
            'source_type': 'tvmaze',
            'description': '',
            'release_year': 2026,
            'rating': 8.0,
            'external_source': 'tvmaze',
            'external_id': title,
            'is_external': True,
            'is_live_source': True,
            'has_direct_watch': has_direct_watch,
            'provider': 'Example Network',
            'network': 'Example Network',
            'access_type': 'other',
            'action_label': 'Watch on Example Network',
            'episode_label': 'S1 E1',
            'airtime': '20:00',
            'runtime': 60,
            'show_type': 'Scripted',
            'is_news': False,
        }

    @patch('core.views.fetch_live_tv_schedule')
    def test_strict_region_defers_metadata_only_tv_to_provider_validation(self, mock_live, *_mocks):
        mock_live.return_value = [
            self._live_item('Watchable Show', has_direct_watch=True),
            self._live_item('Metadata Only Show', has_direct_watch=False),
        ]
        DiscoveryPreference.objects.create(
            user=self.user,
            region='US',
            require_region_availability=True,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Watchable Show')
        self.assertContains(response, 'Metadata Only Show')
        self.assertContains(response, 'data-source-type="tvmaze"')
        self.assertContains(response, 'data-release-year="2026"')
        self.assertContains(response, 'region-pending')
        self.assertContains(response, 'data-require-region="1"')
        self.assertContains(response, 'data-region="US"')

    @patch('core.views.fetch_live_tv_schedule')
    def test_non_strict_discovery_keeps_metadata_only_live_tv_visible(self, mock_live, *_mocks):
        mock_live.return_value = [self._live_item('Metadata Only Show', has_direct_watch=False)]
        DiscoveryPreference.objects.create(
            user=self.user,
            region='US',
            require_region_availability=False,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Metadata Only Show')
        self.assertContains(response, 'Direct watch link not listed by source')
        self.assertNotContains(response, 'card region-pending')
        self.assertContains(response, 'data-require-region="0"')

    @patch('core.views.fetch_live_tv_schedule')
    def test_strict_search_defers_metadata_only_tv_to_same_validation(self, mock_live, *_mocks):
        mock_live.return_value = [
            self._live_item('Watchable Drama', has_direct_watch=True),
            self._live_item('Metadata Drama', has_direct_watch=False),
        ]
        DiscoveryPreference.objects.create(
            user=self.user,
            region='US',
            require_region_availability=True,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('home'), {'q': 'Drama', 'type': 'tv'})

        self.assertContains(response, 'Watchable Drama')
        self.assertContains(response, 'Metadata Drama')
        self.assertContains(response, 'region-pending')
