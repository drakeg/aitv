from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import Airing, Channel, DiscoveryPreference, Program
from core.models import SystemSettings


class StaffGuestPreviewTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username='guest-preview-staff',
            password='test-password',
            is_staff=True,
        )
        DiscoveryPreference.objects.create(
            user=self.staff,
            region='CA',
            preferred_providers=['Netflix'],
            customized=True,
            preferred_genres=['Drama'],
        )
        settings = SystemSettings.load()
        settings.default_region = 'US'
        settings.show_guest_account_links = False
        settings.save()

    @patch('core.views.fetch_popular_tv', return_value=[])
    @patch('core.views.fetch_tv_on_the_air', return_value=[])
    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule', return_value=[])
    def test_staff_home_guest_preview_uses_anonymous_operator_defaults(
        self,
        mock_live,
        *_mocks,
    ):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('home'), {'guest_preview': '1'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['guest_preview_mode'])
        self.assertEqual(response.context['discovery_region'], 'US')
        self.assertFalse(response.context['user'].is_authenticated)
        mock_live.assert_called_once_with(limit=100, country='US')
        self.assertContains(response, 'Guest preview:')
        self.assertContains(response, 'Guest entertainment guide')
        self.assertContains(
            response,
            'href="/live-tv/?guest_preview=1"',
            html=False,
        )
        self.assertContains(response, 'href="#guest-discovery"', html=False)
        self.assertContains(response, 'name="guest_preview" value="1"', html=False)
        self.assertNotContains(response, 'My Watchlist')
        self.assertNotContains(response, '>Operator<', html=False)
        self.assertNotContains(response, 'Hi, guest-preview-staff')

    @patch('core.views.fetch_popular_tv', return_value=[])
    @patch('core.views.fetch_tv_on_the_air', return_value=[])
    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule', return_value=[])
    def test_nonstaff_cannot_force_guest_preview(
        self,
        mock_live,
        *_mocks,
    ):
        user = get_user_model().objects.create_user(
            username='ordinary-preview-user',
            password='test-password',
        )
        DiscoveryPreference.objects.create(user=user, region='CA')
        self.client.force_login(user)

        response = self.client.get(reverse('home'), {'guest_preview': '1'})

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['guest_preview_mode'])
        self.assertEqual(response.context['discovery_region'], 'CA')
        self.assertTrue(response.context['user'].is_authenticated)
        mock_live.assert_called_once_with(limit=100, country='CA')
        self.assertContains(response, 'My Watchlist')
        self.assertNotContains(response, 'Guest preview:')

    def test_staff_live_tv_guest_preview_uses_operator_region_and_guest_controls(self):
        us_channel = Channel.objects.create(
            name='US Preview Network',
            slug='us-preview-network',
            region='US',
            source='tvmaze',
            external_id='us-preview-network',
        )
        ca_channel = Channel.objects.create(
            name='CA Account Network',
            slug='ca-account-network',
            region='CA',
            source='tvmaze',
            external_id='ca-account-network',
        )
        now = timezone.now()
        for channel, suffix in ((us_channel, 'us'), (ca_channel, 'ca')):
            program = Program.objects.create(
                title=f'Preview Show {suffix}',
                source='tvmaze',
                external_id=f'preview-show-{suffix}',
            )
            Airing.objects.create(
                channel=channel,
                program=program,
                starts_at=now - timedelta(minutes=5),
                ends_at=now + timedelta(minutes=25),
                source_schedule_date=timezone.localdate(),
                source='tvmaze',
                external_id=f'preview-airing-{suffix}',
            )
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse('live_tv_guide'),
            {'guest_preview': '1'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['guest_preview_mode'])
        self.assertEqual(response.context['guide_region'], 'US')
        self.assertContains(response, 'US Preview Network')
        self.assertNotContains(response, 'CA Account Network')
        self.assertContains(response, 'name="guest_preview" value="1"', html=False)
        self.assertContains(response, 'guest_preview=1&amp;return_to=', html=False)
        self.assertNotContains(response, '★ Favorites only')
        self.assertNotContains(response, 'guide-favorite')
        self.assertNotContains(response, '>Operator<', html=False)

    def test_staff_channel_schedule_guest_preview_uses_operator_region_and_hides_favorite(self):
        channel = Channel.objects.create(
            name='US Preview Schedule',
            slug='us-preview-schedule',
            region='US',
            source='tvmaze',
            external_id='us-preview-schedule',
        )
        program = Program.objects.create(
            title='Preview Schedule Show',
            source='tvmaze',
            external_id='preview-schedule-show',
        )
        now = timezone.now()
        Airing.objects.create(
            channel=channel,
            program=program,
            starts_at=now - timedelta(minutes=5),
            ends_at=now + timedelta(minutes=25),
            source_schedule_date=timezone.localdate(),
            source='tvmaze',
            external_id='preview-schedule-airing',
        )
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
            {
                'guest_preview': '1',
                'return_to': reverse('live_tv_guide') + '?guest_preview=1',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['guest_preview_mode'])
        self.assertContains(response, 'US Preview Schedule')
        self.assertContains(response, 'guest_preview=1&amp;date=', html=False)
        self.assertContains(response, 'Guest preview:')
        self.assertNotContains(response, 'Add Favorite')
        self.assertNotContains(response, '★ Favorite')
