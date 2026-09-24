from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import Airing, Channel, DiscoveryPreference, Program


class LiveTvGuideTests(TestCase):
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

    def test_guide_shows_now_and_next_without_inventing_watch_action(self):
        channel = Channel.objects.create(
            name='Example Network', slug='example-network', region='US',
            source='tvmaze', external_id='network-1',
        )
        current = Program.objects.create(title='Current Show', source='tvmaze', external_id='show-1')
        upcoming = Program.objects.create(title='Next Show', source='tvmaze', external_id='show-2')
        self._airing(channel, current, timedelta(minutes=-15), timedelta(minutes=15), 'episode-1')
        self._airing(channel, upcoming, timedelta(minutes=15), timedelta(minutes=75), 'episode-2')

        response = self.client.get(reverse('live_tv_guide'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Live TV Guide')
        self.assertContains(response, 'Example Network')
        self.assertContains(response, 'Current Show')
        self.assertContains(response, 'Next Show')
        self.assertContains(response, 'schedule data does not imply playback availability')
        self.assertNotContains(response, '>Watch<', html=False)

    def test_signed_in_guide_uses_account_region(self):
        us_channel = Channel.objects.create(name='US Network', slug='us', region='US', source='tvmaze', external_id='us')
        ca_channel = Channel.objects.create(name='CA Network', slug='ca', region='CA', source='tvmaze', external_id='ca')
        us_program = Program.objects.create(title='US Show', source='tvmaze', external_id='us-show')
        ca_program = Program.objects.create(title='CA Show', source='tvmaze', external_id='ca-show')
        self._airing(us_channel, us_program, timedelta(minutes=-5), timedelta(minutes=25), 'us-airing')
        self._airing(ca_channel, ca_program, timedelta(minutes=-5), timedelta(minutes=25), 'ca-airing')
        user = get_user_model().objects.create_user(username='viewer', password='password')
        DiscoveryPreference.objects.create(user=user, region='CA')
        self.client.force_login(user)

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'CA Network')
        self.assertContains(response, 'CA Show')
        self.assertNotContains(response, 'US Network')
        self.assertNotContains(response, 'US Show')

    def test_guide_has_empty_state_when_no_normalized_schedule_exists(self):
        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'No current guide data is available for US.')
