from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import Airing, Channel, DiscoveryPreference, Program


class LiveTvChannelScheduleTests(TestCase):
    def _airing(self, channel, program, start_delta, end_delta, external_id):
        now = timezone.now()
        return Airing.objects.create(
            channel=channel,
            program=program,
            starts_at=now + start_delta,
            ends_at=now + end_delta,
            source='tvmaze',
            external_id=external_id,
        )

    def test_channel_schedule_shows_current_and_next_12_hours(self):
        channel = Channel.objects.create(
            name='Schedule Network',
            slug='schedule-network',
            region='US',
            source='tvmaze',
            external_id='schedule-network',
        )
        current = Program.objects.create(
            title='Current Schedule Show',
            source='tvmaze',
            external_id='current-schedule-show',
        )
        upcoming = Program.objects.create(
            title='Upcoming Schedule Show',
            source='tvmaze',
            external_id='upcoming-schedule-show',
        )
        beyond_window = Program.objects.create(
            title='Beyond Window Show',
            source='tvmaze',
            external_id='beyond-window-show',
        )
        expired = Program.objects.create(
            title='Expired Schedule Show',
            source='tvmaze',
            external_id='expired-schedule-show',
        )
        self._airing(
            channel, current, timedelta(minutes=-15), timedelta(minutes=45),
            'schedule-current',
        )
        self._airing(
            channel, upcoming, timedelta(hours=2), timedelta(hours=3),
            'schedule-upcoming',
        )
        self._airing(
            channel, beyond_window, timedelta(hours=13), timedelta(hours=14),
            'schedule-beyond-window',
        )
        self._airing(
            channel, expired, timedelta(hours=-2), timedelta(hours=-1),
            'schedule-expired',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Schedule Network')
        self.assertContains(response, 'Current Schedule Show')
        self.assertContains(response, 'Upcoming Schedule Show')
        self.assertNotContains(response, 'Beyond Window Show')
        self.assertNotContains(response, 'Expired Schedule Show')
        self.assertContains(response, 'next 12 hours of normalized schedule data')

    def test_channel_schedule_is_scoped_to_signed_in_region(self):
        us_channel = Channel.objects.create(
            name='US Scoped Network',
            slug='us-scoped-network',
            region='US',
            source='tvmaze',
            external_id='us-scoped-network',
        )
        ca_channel = Channel.objects.create(
            name='CA Scoped Network',
            slug='ca-scoped-network',
            region='CA',
            source='tvmaze',
            external_id='ca-scoped-network',
        )
        user = get_user_model().objects.create_user(
            username='channel-schedule-viewer',
            password='password',
        )
        DiscoveryPreference.objects.create(user=user, region='CA')
        self.client.force_login(user)

        allowed = self.client.get(
            reverse('live_tv_channel_schedule', args=[ca_channel.pk]),
        )
        blocked = self.client.get(
            reverse('live_tv_channel_schedule', args=[us_channel.pk]),
        )

        self.assertEqual(allowed.status_code, 200)
        self.assertContains(allowed, 'CA Scoped Network')
        self.assertEqual(blocked.status_code, 404)

    def test_guide_links_channel_name_to_schedule_detail(self):
        channel = Channel.objects.create(
            name='Linked Schedule Network',
            slug='linked-schedule-network',
            region='US',
            source='tvmaze',
            external_id='linked-schedule-network',
        )
        program = Program.objects.create(
            title='Linked Schedule Show',
            source='tvmaze',
            external_id='linked-schedule-show',
        )
        self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25),
            'linked-schedule-airing',
        )

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(
            response,
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )
