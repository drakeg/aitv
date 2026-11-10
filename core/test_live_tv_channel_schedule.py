from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import Airing, Channel, DiscoveryPreference, Program


class LiveTvChannelScheduleTests(TestCase):
    def _airing(
        self,
        channel,
        program,
        start_delta,
        end_delta,
        external_id,
        *,
        schedule_date=None,
    ):
        now = timezone.now()
        return Airing.objects.create(
            channel=channel,
            program=program,
            starts_at=now + start_delta,
            ends_at=now + end_delta,
            source_schedule_date=schedule_date or timezone.localdate(),
            source='tvmaze',
            external_id=external_id,
        )

    def test_channel_schedule_defaults_to_source_schedule_today(self):
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
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
        tomorrow_program = Program.objects.create(
            title='Tomorrow Schedule Show',
            source='tvmaze',
            external_id='tomorrow-schedule-show',
        )
        expired = Program.objects.create(
            title='Expired Schedule Show',
            source='tvmaze',
            external_id='expired-schedule-show',
        )
        self._airing(
            channel, current, timedelta(minutes=-15), timedelta(minutes=45),
            'schedule-current', schedule_date=today,
        )
        self._airing(
            channel, upcoming, timedelta(hours=2), timedelta(hours=3),
            'schedule-upcoming', schedule_date=today,
        )
        self._airing(
            channel, tomorrow_program, timedelta(days=1, hours=2), timedelta(days=1, hours=3),
            'schedule-tomorrow', schedule_date=tomorrow,
        )
        self._airing(
            channel, expired, timedelta(hours=-2), timedelta(hours=-1),
            'schedule-expired', schedule_date=today,
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Schedule Network')
        self.assertContains(response, 'Current Schedule Show')
        self.assertContains(response, 'Upcoming Schedule Show')
        self.assertContains(response, 'Expired Schedule Show')
        self.assertNotContains(response, 'Tomorrow Schedule Show')
        self.assertContains(response, 'Today')
        self.assertContains(response, 'Tomorrow')
        self.assertContains(response, 'Aired')
        self.assertContains(response, 'Now')
        self.assertContains(response, 'Upcoming')
        self.assertContains(response, 'normalized schedule by source broadcast date')

    def test_channel_schedule_can_select_tomorrow(self):
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        channel = Channel.objects.create(
            name='Tomorrow Network',
            slug='tomorrow-network',
            region='US',
            source='tvmaze',
            external_id='tomorrow-network',
        )
        today_program = Program.objects.create(
            title='Today Program',
            source='tvmaze',
            external_id='today-program',
        )
        tomorrow_program = Program.objects.create(
            title='Tomorrow Program',
            source='tvmaze',
            external_id='tomorrow-program',
        )
        self._airing(
            channel, today_program, timedelta(hours=1), timedelta(hours=2),
            'today-program-airing', schedule_date=today,
        )
        self._airing(
            channel, tomorrow_program, timedelta(days=1, hours=1), timedelta(days=1, hours=2),
            'tomorrow-program-airing', schedule_date=tomorrow,
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
            {'date': tomorrow.isoformat()},
        )

        self.assertContains(response, 'Tomorrow Program')
        self.assertNotContains(response, 'Today Program')
        self.assertContains(response, tomorrow.strftime('%B'))
        self.assertContains(response, str(tomorrow.day))

    def test_channel_schedule_keeps_after_midnight_airing_on_source_airdate(self):
        today = timezone.localdate()
        channel = Channel.objects.create(
            name='Late Night Network',
            slug='late-night-network',
            region='US',
            source='tvmaze',
            external_id='late-night-network',
        )
        program = Program.objects.create(
            title='Late Night Show',
            source='tvmaze',
            external_id='late-night-show',
        )
        midnight = timezone.now().replace(hour=0, minute=35, second=0, microsecond=0) + timedelta(days=1)
        Airing.objects.create(
            channel=channel,
            program=program,
            starts_at=midnight,
            ends_at=midnight + timedelta(hours=1),
            source_schedule_date=today,
            source='tvmaze',
            external_id='late-night-airing',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
            {'date': today.isoformat()},
        )

        self.assertContains(response, 'Late Night Show')

    def test_channel_schedule_rejects_date_outside_configured_horizon(self):
        today = timezone.localdate()
        channel = Channel.objects.create(
            name='Bounded Schedule Network',
            slug='bounded-schedule-network',
            region='US',
            source='tvmaze',
            external_id='bounded-schedule-network',
        )
        program = Program.objects.create(
            title='Bounded Today Show',
            source='tvmaze',
            external_id='bounded-today-show',
        )
        self._airing(
            channel, program, timedelta(hours=1), timedelta(hours=2),
            'bounded-today-airing', schedule_date=today,
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
            {'date': (today + timedelta(days=5)).isoformat()},
        )

        self.assertContains(response, 'Bounded Today Show')

    @patch.dict('os.environ', {'EPG_DAYS': '3'})
    def test_channel_schedule_exposes_configured_third_day(self):
        today = timezone.localdate()
        third_day = today + timedelta(days=2)
        channel = Channel.objects.create(
            name='Three Day Network',
            slug='three-day-network',
            region='US',
            source='tvmaze',
            external_id='three-day-network',
        )
        program = Program.objects.create(
            title='Third Day Show',
            source='tvmaze',
            external_id='third-day-show',
        )
        self._airing(
            channel, program, timedelta(days=2, hours=1), timedelta(days=2, hours=2),
            'third-day-airing', schedule_date=third_day,
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
            {'date': third_day.isoformat()},
        )

        self.assertContains(response, 'Third Day Show')
        self.assertContains(response, f'{third_day:%b} {third_day.day}')

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


    def test_channel_schedule_preserves_filtered_guide_return_path(self):
        channel = Channel.objects.create(
            name='Return Path Network',
            slug='return-path-network',
            region='US',
            source='tvmaze',
            external_id='return-path-network',
        )
        return_to = reverse('live_tv_guide') + '?q=news&category=News&live_now=1'

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
            {'return_to': return_to},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['schedule_return_path'], return_to)
        self.assertContains(response, 'href="' + return_to.replace('&', '&amp;') + '"')

    def test_channel_schedule_rejects_external_return_path(self):
        channel = Channel.objects.create(
            name='Safe Return Network',
            slug='safe-return-network',
            region='US',
            source='tvmaze',
            external_id='safe-return-network',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
            {'return_to': 'https://example.com/not-the-guide'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['schedule_return_path'],
            reverse('live_tv_guide'),
        )
