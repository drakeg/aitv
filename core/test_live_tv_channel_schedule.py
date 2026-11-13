from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import Airing, AiringDestination, Channel, ChannelDestination, ChannelFavorite, ContentAvailability, DiscoveryPreference, EpgRefreshState, Program


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


    def test_signed_in_channel_schedule_can_toggle_favorite_and_return_to_same_day(self):
        user = get_user_model().objects.create_user(
            username='schedule-favorite-viewer',
            password='password',
        )
        self.client.force_login(user)
        channel = Channel.objects.create(
            name='Favorite Schedule Network',
            slug='favorite-schedule-network',
            region='US',
            source='tvmaze',
            external_id='favorite-schedule-network',
        )
        today = timezone.localdate()
        schedule_url = (
            reverse('live_tv_channel_schedule', args=[channel.pk])
            + f'?date={today.isoformat()}'
        )

        response = self.client.post(
            reverse('toggle_channel_favorite', args=[channel.pk]),
            {'return_to': schedule_url},
        )

        self.assertRedirects(response, schedule_url)
        self.assertTrue(
            ChannelFavorite.objects.filter(user=user, channel=channel).exists()
        )

        page = self.client.get(schedule_url)
        self.assertTrue(page.context['schedule_is_favorite'])
        self.assertContains(page, '★ Favorite')

    def test_favorite_toggle_rejects_channel_outside_signed_in_region(self):
        user = get_user_model().objects.create_user(
            username='region-favorite-viewer',
            password='password',
        )
        DiscoveryPreference.objects.create(user=user, region='CA')
        self.client.force_login(user)
        us_channel = Channel.objects.create(
            name='US Favorite Network',
            slug='us-favorite-network',
            region='US',
            source='tvmaze',
            external_id='us-favorite-network',
        )

        response = self.client.post(
            reverse('toggle_channel_favorite', args=[us_channel.pk]),
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            ChannelFavorite.objects.filter(user=user, channel=us_channel).exists()
        )


    def test_channel_schedule_loads_shared_auto_refresh_script(self):
        channel = Channel.objects.create(
            name='Refresh Schedule Network',
            slug='refresh-schedule-network',
            region='US',
            source='tvmaze',
            external_id='refresh-schedule-network',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'js/live-tv-auto-refresh.js')


    def test_channel_schedule_shows_trusted_destination_for_current_airing_only(self):
        channel = Channel.objects.create(
            name='Playable Schedule Network',
            slug='playable-schedule-network',
            region='US',
            source='tvmaze',
            external_id='playable-schedule-network',
        )
        current_program = Program.objects.create(
            title='Playable Current Show',
            source='tvmaze',
            external_id='playable-current-show',
        )
        future_program = Program.objects.create(
            title='Future No Play Show',
            source='tvmaze',
            external_id='future-no-play-show',
        )
        current_airing = self._airing(
            channel, current_program, timedelta(minutes=-5), timedelta(minutes=25),
            'playable-current-airing',
        )
        future_airing = self._airing(
            channel, future_program, timedelta(minutes=30), timedelta(minutes=60),
            'future-no-play-airing',
        )
        AiringDestination.objects.create(
            airing=current_airing,
            provider='Example Provider',
            url='https://example.com/current',
            access_type=ContentAvailability.AccessType.FREE,
            scope=AiringDestination.Scope.EPISODE,
            source='tvmaze',
        )
        AiringDestination.objects.create(
            airing=future_airing,
            provider='Future Provider',
            url='https://example.com/future',
            access_type=ContentAvailability.AccessType.FREE,
            scope=AiringDestination.Scope.EPISODE,
            source='tvmaze',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertContains(response, 'Watch on Example Provider')
        self.assertContains(response, 'Episode destination')
        self.assertNotContains(response, 'Watch on Future Provider')
        self.assertNotContains(response, 'https://example.com/future')

    def test_channel_schedule_falls_back_to_trusted_channel_destination(self):
        channel = Channel.objects.create(
            name='Channel Destination Network',
            slug='channel-destination-network',
            region='US',
            source='tvmaze',
            external_id='channel-destination-network',
        )
        program = Program.objects.create(
            title='Channel Destination Show',
            source='tvmaze',
            external_id='channel-destination-show',
        )
        self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25),
            'channel-destination-airing',
        )
        ChannelDestination.objects.create(
            channel=channel,
            provider='Channel Provider',
            url='https://example.com/channel',
            access_type=ContentAvailability.AccessType.AUTH,
            destination_type=ChannelDestination.DestinationType.DIRECT,
            source='operator',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertContains(response, 'Channel Provider · Sign-in required')
        self.assertNotContains(response, 'Episode destination')
        self.assertNotContains(response, 'Show destination')


    def test_channel_schedule_shows_rounded_current_airing_countdown(self):
        channel = Channel.objects.create(
            name='Countdown Schedule Network',
            slug='countdown-schedule-network',
            region='US',
            source='tvmaze',
            external_id='countdown-schedule-network',
        )
        program = Program.objects.create(
            title='Countdown Current Show',
            source='tvmaze',
            external_id='countdown-current-show',
        )
        self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25, seconds=1),
            'countdown-current-airing',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['schedule_current_ends_in_minutes'], 26)
        self.assertContains(response, 'Ends in 26 min')

    def test_channel_schedule_does_not_show_countdown_for_future_only_airings(self):
        channel = Channel.objects.create(
            name='Future Countdown Network',
            slug='future-countdown-network',
            region='US',
            source='tvmaze',
            external_id='future-countdown-network',
        )
        program = Program.objects.create(
            title='Future Countdown Show',
            source='tvmaze',
            external_id='future-countdown-show',
        )
        self._airing(
            channel, program, timedelta(minutes=20), timedelta(minutes=50),
            'future-countdown-airing',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertIsNone(response.context['schedule_current_ends_in_minutes'])
        self.assertNotContains(response, 'Ends in ')


    def test_channel_schedule_shows_rounded_countdown_for_next_airing_within_hour(self):
        channel = Channel.objects.create(
            name='Starts Soon Schedule Network',
            slug='starts-soon-schedule-network',
            region='US',
            source='tvmaze',
            external_id='starts-soon-schedule-network',
        )
        first_program = Program.objects.create(
            title='Starts Soon First Show',
            source='tvmaze',
            external_id='starts-soon-first-show',
        )
        later_program = Program.objects.create(
            title='Starts Soon Later Show',
            source='tvmaze',
            external_id='starts-soon-later-show',
        )
        first_airing = self._airing(
            channel, first_program, timedelta(minutes=20, seconds=1), timedelta(minutes=50),
            'starts-soon-first-airing',
        )
        self._airing(
            channel, later_program, timedelta(minutes=40), timedelta(minutes=70),
            'starts-soon-later-airing',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['schedule_next_airing_id'], first_airing.id)
        self.assertEqual(response.context['schedule_next_starts_in_minutes'], 21)
        self.assertContains(response, 'Starts in 21 min', count=1)

    def test_channel_schedule_labels_next_airing_when_over_hour_away(self):
        channel = Channel.objects.create(
            name='Later Schedule Network',
            slug='later-schedule-network',
            region='US',
            source='tvmaze',
            external_id='later-schedule-network',
        )
        program = Program.objects.create(
            title='Later Schedule Show',
            source='tvmaze',
            external_id='later-schedule-show',
        )
        next_airing = self._airing(
            channel, program, timedelta(minutes=61), timedelta(minutes=91),
            'later-schedule-airing',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertEqual(response.context['schedule_next_airing_id'], next_airing.id)
        self.assertIsNone(response.context['schedule_next_starts_in_minutes'])
        self.assertContains(response, '>Next<', count=1, html=False)
        self.assertNotContains(response, '>Upcoming<', html=False)
        self.assertNotContains(response, 'Starts in ')


    def test_channel_schedule_surfaces_missing_epg_refresh_state(self):
        channel = Channel.objects.create(
            name='Missing Health Network',
            slug='missing-health-network',
            region='US',
            source='tvmaze',
            external_id='missing-health-network',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertTrue(response.context['epg_refresh_missing'])
        self.assertContains(
            response,
            'Guide refresh status is not available yet.',
        )

    def test_channel_schedule_surfaces_failed_epg_refresh_state(self):
        channel = Channel.objects.create(
            name='Failed Health Network',
            slug='failed-health-network',
            region='US',
            source='tvmaze',
            external_id='failed-health-network',
        )
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            refreshed_at=timezone.now() - timedelta(minutes=30),
            airing_count=42,
            attempted_at=timezone.now(),
            status=EpgRefreshState.Status.FAILURE,
            last_error='upstream failure',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertTrue(response.context['epg_refresh_failed'])
        self.assertContains(
            response,
            'The latest EPG refresh attempt failed.',
        )
        self.assertNotContains(response, 'upstream failure')

    @patch.dict('os.environ', {'EPG_STALE_AFTER_SECONDS': '60'})
    def test_channel_schedule_surfaces_stale_epg_refresh_state(self):
        channel = Channel.objects.create(
            name='Stale Health Network',
            slug='stale-health-network',
            region='US',
            source='tvmaze',
            external_id='stale-health-network',
        )
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            refreshed_at=timezone.now() - timedelta(minutes=5),
            airing_count=12,
            attempted_at=timezone.now() - timedelta(minutes=5),
            status=EpgRefreshState.Status.SUCCESS,
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertTrue(response.context['epg_is_stale'])
        self.assertContains(response, 'Guide data may be stale')
        self.assertContains(response, '12 airings')


    def test_guide_and_channel_schedule_share_preferred_destination_selection(self):
        user = get_user_model().objects.create_user(
            username='shared-destination-viewer',
            password='password',
        )
        DiscoveryPreference.objects.create(
            user=user,
            region='US',
            preferred_providers=['Amazon Prime Video'],
        )
        self.client.force_login(user)
        channel = Channel.objects.create(
            name='Shared Destination Network',
            slug='shared-destination-network',
            region='US',
            source='tvmaze',
            external_id='shared-destination-network',
        )
        program = Program.objects.create(
            title='Shared Destination Show',
            source='tvmaze',
            external_id='shared-destination-show',
        )
        airing = self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25),
            'shared-destination-airing',
        )
        AiringDestination.objects.create(
            airing=airing,
            provider='Other Provider',
            url='https://example.com/shared/other',
            access_type=ContentAvailability.AccessType.FREE,
            scope=AiringDestination.Scope.EPISODE,
            source='fixture',
        )
        AiringDestination.objects.create(
            airing=airing,
            provider='Prime Video',
            url='https://example.com/shared/prime',
            access_type=ContentAvailability.AccessType.SUBSCRIPTION,
            scope=AiringDestination.Scope.EPISODE,
            source='fixture',
        )

        guide = self.client.get(reverse('live_tv_guide'))
        schedule = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        for response in (guide, schedule):
            self.assertContains(response, 'Prime Video · Subscription')
            self.assertContains(response, 'https://example.com/shared/prime')
            self.assertNotContains(response, 'https://example.com/shared/other')


    def test_channel_schedule_uses_shared_epg_health_partial(self):
        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[
                Channel.objects.create(
                    name='Shared Health Partial Network',
                    slug='shared-health-partial-network',
                    region='US',
                    source='tvmaze',
                    external_id='shared-health-partial-network',
                ).pk
            ]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'live_tv/_epg_health.html')


    def test_channel_schedule_does_not_show_empty_refresh_age_after_first_refresh_failure(self):
        channel = Channel.objects.create(
            name='First Failure Network',
            slug='first-failure-network',
            region='US',
            source='tvmaze',
            external_id='first-failure-network',
        )
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            refreshed_at=None,
            airing_count=0,
            attempted_at=timezone.now(),
            status=EpgRefreshState.Status.FAILURE,
            last_error='initial upstream failure',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertContains(response, 'The latest EPG refresh attempt failed.')
        self.assertNotContains(response, 'Guide refreshed')
        self.assertNotContains(response, 'initial upstream failure')


    def test_channel_schedule_labels_earliest_future_airing_next_beyond_one_hour(self):
        channel = Channel.objects.create(
            name='Next Label Network',
            slug='next-label-network',
            region='US',
            source='tvmaze',
            external_id='next-label-network',
        )
        next_program = Program.objects.create(
            title='Next Label Show',
            source='tvmaze',
            external_id='next-label-show',
        )
        later_program = Program.objects.create(
            title='Later Upcoming Show',
            source='tvmaze',
            external_id='later-upcoming-show',
        )
        self._airing(
            channel,
            next_program,
            timedelta(minutes=90),
            timedelta(minutes=120),
            'next-label-airing',
        )
        self._airing(
            channel,
            later_program,
            timedelta(minutes=150),
            timedelta(minutes=180),
            'later-upcoming-airing',
        )

        response = self.client.get(
            reverse('live_tv_channel_schedule', args=[channel.pk]),
        )

        self.assertContains(response, '>Next<', count=1, html=False)
        self.assertContains(response, '>Upcoming<', count=1, html=False)
        self.assertNotContains(response, 'Starts in')
