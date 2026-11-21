from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import Airing, Channel, DiscoveryPreference, Program
from core.models import SystemSettings


class GuestDefaultRegionTests(TestCase):
    def _current_airing(self, channel, suffix):
        program = Program.objects.create(
            title=f'Region Program {suffix}',
            source='tvmaze',
            external_id=f'region-program-{suffix}',
        )
        now = timezone.now()
        return Airing.objects.create(
            channel=channel,
            program=program,
            starts_at=now - timedelta(minutes=5),
            ends_at=now + timedelta(minutes=25),
            source_schedule_date=timezone.localdate(),
            source='tvmaze',
            external_id=f'region-airing-{suffix}',
        )

    @patch('core.views.fetch_popular_tv', return_value=[])
    @patch('core.views.fetch_tv_on_the_air', return_value=[])
    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule', return_value=[])
    def test_anonymous_discovery_uses_operator_default_region(self, mock_live, *_mocks):
        settings = SystemSettings.load()
        settings.default_region = 'CA'
        settings.save()

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['discovery_region'], 'CA')
        mock_live.assert_called_once_with(limit=100, country='CA')

    @patch('core.views.fetch_popular_tv', return_value=[])
    @patch('core.views.fetch_tv_on_the_air', return_value=[])
    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule', return_value=[])
    def test_signed_in_region_preference_overrides_operator_default(self, mock_live, *_mocks):
        settings = SystemSettings.load()
        settings.default_region = 'CA'
        settings.save()
        user = get_user_model().objects.create_user(
            username='region-override-viewer',
            password='test-password',
        )
        DiscoveryPreference.objects.create(user=user, region='US')
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.context['discovery_region'], 'US')
        mock_live.assert_called_once_with(limit=100, country='US')

    def test_anonymous_live_tv_guide_uses_operator_default_region(self):
        settings = SystemSettings.load()
        settings.default_region = 'CA'
        settings.save()
        ca_channel = Channel.objects.create(
            name='Canada Guest Network',
            slug='canada-guest-network',
            region='CA',
            source='tvmaze',
            external_id='canada-guest-network',
        )
        us_channel = Channel.objects.create(
            name='US Guest Network',
            slug='us-guest-network',
            region='US',
            source='tvmaze',
            external_id='us-guest-network',
        )
        self._current_airing(ca_channel, 'ca')
        self._current_airing(us_channel, 'us')

        response = self.client.get(reverse('live_tv_guide'))

        self.assertEqual(response.context['guide_region'], 'CA')
        self.assertContains(response, 'Canada Guest Network')
        self.assertNotContains(response, 'US Guest Network')

    def test_anonymous_channel_schedule_enforces_operator_default_region(self):
        settings = SystemSettings.load()
        settings.default_region = 'CA'
        settings.save()
        ca_channel = Channel.objects.create(
            name='Canada Schedule Network',
            slug='canada-schedule-network',
            region='CA',
            source='tvmaze',
            external_id='canada-schedule-network',
        )
        us_channel = Channel.objects.create(
            name='US Schedule Network',
            slug='us-schedule-network',
            region='US',
            source='tvmaze',
            external_id='us-schedule-network',
        )
        self._current_airing(ca_channel, 'schedule-ca')
        self._current_airing(us_channel, 'schedule-us')

        allowed = self.client.get(
            reverse('live_tv_channel_schedule', args=[ca_channel.pk]),
        )
        denied = self.client.get(
            reverse('live_tv_channel_schedule', args=[us_channel.pk]),
        )

        self.assertEqual(allowed.status_code, 200)
        self.assertContains(allowed, 'Canada Schedule Network')
        self.assertEqual(denied.status_code, 404)
