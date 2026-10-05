from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import Airing, AiringDestination, Channel, ChannelDestination, ChannelFavorite, DiscoveryPreference, EpgRefreshState, Program


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

    def test_guide_shows_now_next_and_later_programs(self):
        channel = Channel.objects.create(
            name='Three Slot Network', slug='three-slot-network', region='US',
            source='tvmaze', external_id='three-slot-network',
        )
        current = Program.objects.create(
            title='Current Slot Show', source='tvmaze', external_id='current-slot-show',
        )
        next_program = Program.objects.create(
            title='Next Slot Show', source='tvmaze', external_id='next-slot-show',
        )
        later_program = Program.objects.create(
            title='Later Slot Show', source='tvmaze', external_id='later-slot-show',
        )
        self._airing(
            channel, current, timedelta(minutes=-10), timedelta(minutes=20),
            'three-slot-current',
        )
        self._airing(
            channel, next_program, timedelta(minutes=20), timedelta(minutes=80),
            'three-slot-next',
        )
        self._airing(
            channel, later_program, timedelta(minutes=80), timedelta(minutes=140),
            'three-slot-later',
        )

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'Current Slot Show')
        self.assertContains(response, 'Next Slot Show')
        self.assertContains(response, 'Later Slot Show')
        self.assertContains(response, '<span class="guide-label">Later</span>', html=True)

    def test_guide_later_slot_uses_second_future_airing_only(self):
        channel = Channel.objects.create(
            name='Later Ordering Network', slug='later-ordering-network', region='US',
            source='tvmaze', external_id='later-ordering-network',
        )
        first = Program.objects.create(
            title='First Future', source='tvmaze', external_id='first-future',
        )
        second = Program.objects.create(
            title='Second Future', source='tvmaze', external_id='second-future',
        )
        third = Program.objects.create(
            title='Third Future', source='tvmaze', external_id='third-future',
        )
        self._airing(
            channel, first, timedelta(minutes=10), timedelta(minutes=40),
            'later-order-first',
        )
        self._airing(
            channel, second, timedelta(minutes=40), timedelta(minutes=70),
            'later-order-second',
        )
        self._airing(
            channel, third, timedelta(minutes=70), timedelta(minutes=100),
            'later-order-third',
        )

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'First Future')
        self.assertContains(response, 'Second Future')
        self.assertNotContains(response, 'Third Future')

    def test_guide_shows_only_explicit_playable_channel_destination(self):
        channel = Channel.objects.create(
            name='Playable Network', slug='playable-network', region='US',
            source='tvmaze', external_id='playable-network',
        )
        program = Program.objects.create(title='Playable Show', source='tvmaze', external_id='playable-show')
        self._airing(channel, program, timedelta(minutes=-5), timedelta(minutes=25), 'playable-airing')
        ChannelDestination.objects.create(
            channel=channel,
            provider='Example Stream',
            url='https://example.com/live',
            access_type='free',
            destination_type=ChannelDestination.DestinationType.DIRECT,
            source='fixture',
        )

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'Watch on Example Stream')
        self.assertContains(response, 'https://example.com/live')

    def test_current_airing_destination_precedes_channel_destination(self):
        channel = Channel.objects.create(
            name='Airing Network', slug='airing-network', region='US',
            source='tvmaze', external_id='airing-network',
        )
        program = Program.objects.create(title='Airing Show', source='tvmaze', external_id='airing-show')
        airing = self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25), 'airing-destination',
        )
        ChannelDestination.objects.create(
            channel=channel,
            provider='Channel Stream',
            url='https://example.com/channel',
            access_type='free',
            destination_type=ChannelDestination.DestinationType.DIRECT,
            source='fixture',
        )
        AiringDestination.objects.create(
            airing=airing,
            provider='ABC',
            url='https://abc.com/episode/example',
            access_type='other',
            scope=AiringDestination.Scope.EPISODE,
            source='tvmaze',
        )

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'Watch on ABC')
        self.assertContains(response, 'https://abc.com/episode/example')
        self.assertNotContains(response, 'https://example.com/channel')

    def test_preferred_provider_ranks_multiple_episode_destinations(self):
        channel = Channel.objects.create(
            name='Preferred Airing Network', slug='preferred-airing-network', region='US',
            source='tvmaze', external_id='preferred-airing-network',
        )
        program = Program.objects.create(
            title='Preferred Airing Show', source='tvmaze', external_id='preferred-airing-show',
        )
        airing = self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25),
            'preferred-airing-destination',
        )
        AiringDestination.objects.create(
            airing=airing,
            provider='Other Provider',
            url='https://example.com/episode/other',
            access_type='free',
            scope=AiringDestination.Scope.EPISODE,
            source='fixture',
        )
        AiringDestination.objects.create(
            airing=airing,
            provider='Prime Video',
            url='https://example.com/episode/prime',
            access_type='subscription',
            scope=AiringDestination.Scope.EPISODE,
            source='fixture',
        )
        user = get_user_model().objects.create_user(
            username='airing-provider-viewer', password='password',
        )
        DiscoveryPreference.objects.create(
            user=user,
            region='US',
            preferred_providers=['Amazon Prime Video'],
        )
        self.client.force_login(user)

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'Prime Video · Subscription')
        self.assertContains(response, 'https://example.com/episode/prime')
        self.assertNotContains(response, 'https://example.com/episode/other')

    def test_episode_scope_precedes_preferred_show_destination(self):
        channel = Channel.objects.create(
            name='Scope Network', slug='scope-network', region='US',
            source='tvmaze', external_id='scope-network',
        )
        program = Program.objects.create(
            title='Scope Show', source='tvmaze', external_id='scope-show',
        )
        airing = self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25),
            'scope-airing-destination',
        )
        AiringDestination.objects.create(
            airing=airing,
            provider='ABC',
            url='https://abc.com/episode/scope',
            access_type='other',
            scope=AiringDestination.Scope.EPISODE,
            source='fixture',
        )
        AiringDestination.objects.create(
            airing=airing,
            provider='Prime Video',
            url='https://example.com/show/prime',
            access_type='subscription',
            scope=AiringDestination.Scope.SHOW,
            source='fixture',
        )
        user = get_user_model().objects.create_user(
            username='scope-viewer', password='password',
        )
        DiscoveryPreference.objects.create(
            user=user,
            region='US',
            preferred_providers=['Amazon Prime Video'],
        )
        self.client.force_login(user)

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'Watch on ABC')
        self.assertContains(response, 'https://abc.com/episode/scope')
        self.assertNotContains(response, 'https://example.com/show/prime')

    def test_episode_destination_scope_is_visible_in_guide(self):
        channel = Channel.objects.create(
            name='Episode Scope Network', slug='episode-scope-network', region='US',
            source='tvmaze', external_id='episode-scope-network',
        )
        program = Program.objects.create(
            title='Episode Scope Show', source='tvmaze', external_id='episode-scope-show',
        )
        airing = self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25),
            'episode-scope-airing',
        )
        AiringDestination.objects.create(
            airing=airing,
            provider='ABC',
            url='https://abc.com/episode/scope-visible',
            access_type='other',
            scope=AiringDestination.Scope.EPISODE,
            source='fixture',
        )

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'Episode destination')
        self.assertContains(response, 'This destination applies to the current episode only.')

    def test_show_destination_scope_is_visible_in_guide(self):
        channel = Channel.objects.create(
            name='Show Scope Network', slug='show-scope-network', region='US',
            source='tvmaze', external_id='show-scope-network',
        )
        program = Program.objects.create(
            title='Show Scope Show', source='tvmaze', external_id='show-scope-show',
        )
        airing = self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25),
            'show-scope-airing',
        )
        AiringDestination.objects.create(
            airing=airing,
            provider='Prime Video',
            url='https://example.com/show/scope-visible',
            access_type='subscription',
            scope=AiringDestination.Scope.SHOW,
            source='fixture',
        )

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'Show destination')
        self.assertContains(response, "This destination applies to the current show's provider page.")

    def test_channel_destination_does_not_claim_airing_scope(self):
        channel = Channel.objects.create(
            name='Channel Scope Network', slug='channel-scope-network', region='US',
            source='tvmaze', external_id='channel-scope-network',
        )
        program = Program.objects.create(
            title='Channel Scope Show', source='tvmaze', external_id='channel-scope-show',
        )
        self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25),
            'channel-scope-airing',
        )
        ChannelDestination.objects.create(
            channel=channel,
            provider='Channel Provider',
            url='https://example.com/channel/scope',
            access_type='free',
            destination_type=ChannelDestination.DestinationType.DIRECT,
            source='fixture',
        )

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'Watch on Channel Provider')
        self.assertNotContains(response, 'Episode destination')
        self.assertNotContains(response, 'Show destination')

    def test_playable_only_filter_includes_explicit_channel_destination(self):
        playable_channel = Channel.objects.create(
            name='Playable Filter Network', slug='playable-filter-network', region='US',
            source='tvmaze', external_id='playable-filter-network',
        )
        metadata_channel = Channel.objects.create(
            name='Metadata Filter Network', slug='metadata-filter-network', region='US',
            source='tvmaze', external_id='metadata-filter-network',
        )
        playable_program = Program.objects.create(
            title='Playable Filter Show', source='tvmaze', external_id='playable-filter-show',
        )
        metadata_program = Program.objects.create(
            title='Metadata Filter Show', source='tvmaze', external_id='metadata-filter-show',
        )
        self._airing(
            playable_channel, playable_program, timedelta(minutes=-5), timedelta(minutes=25),
            'playable-filter-airing',
        )
        self._airing(
            metadata_channel, metadata_program, timedelta(minutes=-5), timedelta(minutes=25),
            'metadata-filter-airing',
        )
        ChannelDestination.objects.create(
            channel=playable_channel,
            provider='Playable Provider',
            url='https://example.com/playable-filter',
            access_type='free',
            destination_type=ChannelDestination.DestinationType.DIRECT,
            source='fixture',
        )
        ChannelDestination.objects.create(
            channel=metadata_channel,
            provider='Metadata Provider',
            url='https://example.com/metadata-filter',
            access_type='other',
            destination_type=ChannelDestination.DestinationType.DETAILS,
            source='fixture',
        )

        response = self.client.get(reverse('live_tv_guide'), {'playable': '1'})

        self.assertContains(response, 'Playable Filter Network')
        self.assertContains(response, 'Watch on Playable Provider')
        self.assertNotContains(response, 'Metadata Filter Network')
        self.assertNotContains(response, 'Metadata Filter Show')
        self.assertContains(response, 'name="playable" value="1" checked', html=False)

    def test_playable_only_filter_excludes_channel_destination_without_current_airing(self):
        channel = Channel.objects.create(
            name='Future Only Playable Network', slug='future-only-playable-network', region='US',
            source='tvmaze', external_id='future-only-playable-network',
        )
        program = Program.objects.create(
            title='Future Only Playable Show', source='tvmaze', external_id='future-only-playable-show',
        )
        self._airing(
            channel, program, timedelta(minutes=20), timedelta(minutes=80),
            'future-only-playable-airing',
        )
        ChannelDestination.objects.create(
            channel=channel,
            provider='Future Channel Provider',
            url='https://example.com/future-only-playable',
            access_type='free',
            destination_type=ChannelDestination.DestinationType.DIRECT,
            source='fixture',
        )

        response = self.client.get(reverse('live_tv_guide'), {'playable': '1'})

        self.assertNotContains(response, 'Future Only Playable Network')
        self.assertNotContains(response, 'Future Only Playable Show')
        self.assertContains(response, 'No channels match the active Live TV filters for US.')

    def test_playable_only_filter_includes_current_airing_destination(self):
        channel = Channel.objects.create(
            name='Airing Playable Filter Network', slug='airing-playable-filter-network', region='US',
            source='tvmaze', external_id='airing-playable-filter-network',
        )
        program = Program.objects.create(
            title='Airing Playable Filter Show', source='tvmaze',
            external_id='airing-playable-filter-show',
        )
        airing = self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25),
            'airing-playable-filter-airing',
        )
        AiringDestination.objects.create(
            airing=airing,
            provider='ABC',
            url='https://abc.com/episode/playable-filter',
            access_type='other',
            scope=AiringDestination.Scope.EPISODE,
            source='tvmaze',
        )

        response = self.client.get(reverse('live_tv_guide'), {'playable': '1'})

        self.assertContains(response, 'Airing Playable Filter Network')
        self.assertContains(response, 'Episode destination')
        self.assertContains(response, 'Watch on ABC')

    def test_playable_only_filter_does_not_treat_next_airing_destination_as_playable_now(self):
        channel = Channel.objects.create(
            name='Future Destination Network', slug='future-destination-network', region='US',
            source='tvmaze', external_id='future-destination-network',
        )
        current = Program.objects.create(
            title='Current Metadata Show', source='tvmaze', external_id='current-metadata-show',
        )
        future = Program.objects.create(
            title='Future Destination Show', source='tvmaze', external_id='future-destination-show',
        )
        self._airing(
            channel, current, timedelta(minutes=-5), timedelta(minutes=25),
            'current-metadata-airing',
        )
        future_airing = self._airing(
            channel, future, timedelta(minutes=25), timedelta(minutes=85),
            'future-destination-airing',
        )
        AiringDestination.objects.create(
            airing=future_airing,
            provider='ABC',
            url='https://abc.com/episode/future-only',
            access_type='other',
            scope=AiringDestination.Scope.EPISODE,
            source='tvmaze',
        )

        response = self.client.get(reverse('live_tv_guide'), {'playable': '1'})

        self.assertNotContains(response, 'Future Destination Network')
        self.assertContains(response, 'No channels match the active Live TV filters for US.')

    def test_metadata_destination_does_not_create_watch_action(self):
        channel = Channel.objects.create(
            name='Metadata Network', slug='metadata-network', region='US',
            source='tvmaze', external_id='metadata-network',
        )
        program = Program.objects.create(title='Metadata Show', source='tvmaze', external_id='metadata-show')
        self._airing(channel, program, timedelta(minutes=-5), timedelta(minutes=25), 'metadata-airing')
        ChannelDestination.objects.create(
            channel=channel,
            provider='Example Provider',
            url='https://example.com/details',
            access_type='other',
            destination_type=ChannelDestination.DestinationType.DETAILS,
            source='fixture',
        )

        response = self.client.get(reverse('live_tv_guide'))

        self.assertNotContains(response, 'https://example.com/details')
        self.assertNotContains(response, 'Watch on Example Provider')

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

    def test_guide_warns_when_refresh_state_is_missing(self):
        channel = Channel.objects.create(
            name='Untracked Network', slug='untracked-network', region='US',
            source='tvmaze', external_id='untracked-network',
        )
        program = Program.objects.create(
            title='Untracked Show', source='tvmaze', external_id='untracked-show',
        )
        self._airing(
            channel, program, timedelta(minutes=-5), timedelta(minutes=25), 'untracked-airing',
        )

        response = self.client.get(reverse('live_tv_guide'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Guide refresh status is not available yet')
        self.assertNotContains(response, 'The latest EPG refresh attempt failed')
        self.assertNotContains(response, 'Guide data may be stale because')

    def test_guide_shows_refresh_age_and_stale_warning(self):
        channel = Channel.objects.create(
            name='Freshness Network', slug='freshness-network', region='US',
            source='tvmaze', external_id='freshness-network',
        )
        program = Program.objects.create(title='Freshness Show', source='tvmaze', external_id='freshness-show')
        self._airing(channel, program, timedelta(minutes=-5), timedelta(minutes=25), 'freshness-airing')
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            refreshed_at=timezone.now() - timedelta(hours=3),
            airing_count=9,
        )

        with self.settings():
            response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'Guide refreshed')
        self.assertContains(response, '9 airings')
        self.assertContains(response, 'Guide data may be stale')

    def test_guide_shows_latest_refresh_failure_without_exposing_error_details(self):
        channel = Channel.objects.create(
            name='Failure Network', slug='failure-network', region='US',
            source='tvmaze', external_id='failure-network',
        )
        program = Program.objects.create(title='Failure Show', source='tvmaze', external_id='failure-show')
        self._airing(channel, program, timedelta(minutes=-5), timedelta(minutes=25), 'failure-airing')
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            refreshed_at=timezone.now() - timedelta(minutes=30),
            attempted_at=timezone.now() - timedelta(minutes=1),
            airing_count=11,
            status=EpgRefreshState.Status.FAILURE,
            last_error='RuntimeError: secret upstream detail',
        )

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'The latest EPG refresh attempt failed')
        self.assertContains(response, '11 airings')
        self.assertNotContains(response, 'secret upstream detail')

    def test_signed_in_viewer_can_toggle_channel_favorite(self):
        channel = Channel.objects.create(
            name='Favorite Network', slug='favorite-network', region='US',
            source='tvmaze', external_id='favorite-network',
        )
        user = get_user_model().objects.create_user(username='favorite-viewer', password='password')
        self.client.force_login(user)
        url = reverse('toggle_channel_favorite', args=[channel.pk])

        response = self.client.post(url)
        self.assertRedirects(response, reverse('live_tv_guide'))
        self.assertTrue(ChannelFavorite.objects.filter(user=user, channel=channel).exists())

        response = self.client.post(url)
        self.assertRedirects(response, reverse('live_tv_guide'))
        self.assertFalse(ChannelFavorite.objects.filter(user=user, channel=channel).exists())

    def test_channel_favorite_action_preserves_playable_filter(self):
        channel = Channel.objects.create(
            name='Playable Favorite Network', slug='playable-favorite-network', region='US',
            source='tvmaze', external_id='playable-favorite-network',
        )
        user = get_user_model().objects.create_user(
            username='playable-favorite-viewer', password='password',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('toggle_channel_favorite', args=[channel.pk]),
            {'playable': '1'},
        )

        self.assertRedirects(response, f"{reverse('live_tv_guide')}?playable=1")

    def test_channel_favorite_action_requires_authentication_and_post(self):
        channel = Channel.objects.create(
            name='Protected Network', slug='protected-network', region='US',
            source='tvmaze', external_id='protected-network',
        )
        url = reverse('toggle_channel_favorite', args=[channel.pk])

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        self.assertFalse(ChannelFavorite.objects.exists())

        user = get_user_model().objects.create_user(username='post-only-viewer', password='password')
        self.client.force_login(user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        self.assertFalse(ChannelFavorite.objects.exists())

    def test_signed_in_guide_prioritizes_favorite_channels(self):
        alpha_channel = Channel.objects.create(
            name='Alpha Network', slug='alpha-priority-network', region='US',
            source='tvmaze', external_id='alpha-priority-network',
        )
        zulu_channel = Channel.objects.create(
            name='Zulu Network', slug='zulu-priority-network', region='US',
            source='tvmaze', external_id='zulu-priority-network',
        )
        alpha_program = Program.objects.create(
            title='Alpha Show', source='tvmaze', external_id='alpha-priority-show',
        )
        zulu_program = Program.objects.create(
            title='Zulu Show', source='tvmaze', external_id='zulu-priority-show',
        )
        self._airing(
            alpha_channel, alpha_program, timedelta(minutes=-5), timedelta(minutes=25),
            'alpha-priority-airing',
        )
        self._airing(
            zulu_channel, zulu_program, timedelta(minutes=-5), timedelta(minutes=25),
            'zulu-priority-airing',
        )
        user = get_user_model().objects.create_user(username='priority-viewer', password='password')
        ChannelFavorite.objects.create(user=user, channel=zulu_channel)
        self.client.force_login(user)

        response = self.client.get(reverse('live_tv_guide'))

        content = response.content.decode()
        self.assertLess(content.index('Zulu Network'), content.index('Alpha Network'))

    def test_anonymous_guide_keeps_alphabetical_channel_order(self):
        alpha_channel = Channel.objects.create(
            name='Alpha Public', slug='alpha-public-network', region='US',
            source='tvmaze', external_id='alpha-public-network',
        )
        zulu_channel = Channel.objects.create(
            name='Zulu Public', slug='zulu-public-network', region='US',
            source='tvmaze', external_id='zulu-public-network',
        )
        alpha_program = Program.objects.create(
            title='Alpha Public Show', source='tvmaze', external_id='alpha-public-show',
        )
        zulu_program = Program.objects.create(
            title='Zulu Public Show', source='tvmaze', external_id='zulu-public-show',
        )
        self._airing(
            alpha_channel, alpha_program, timedelta(minutes=-5), timedelta(minutes=25),
            'alpha-public-airing',
        )
        self._airing(
            zulu_channel, zulu_program, timedelta(minutes=-5), timedelta(minutes=25),
            'zulu-public-airing',
        )

        response = self.client.get(reverse('live_tv_guide'))

        content = response.content.decode()
        self.assertLess(content.index('Alpha Public'), content.index('Zulu Public'))

    def test_favorites_only_filter_is_scoped_to_signed_in_user(self):
        favorite_channel = Channel.objects.create(
            name='My Network', slug='my-network', region='US',
            source='tvmaze', external_id='my-network',
        )
        other_channel = Channel.objects.create(
            name='Other Network', slug='other-network', region='US',
            source='tvmaze', external_id='other-network',
        )
        favorite_program = Program.objects.create(
            title='My Show', source='tvmaze', external_id='my-show',
        )
        other_program = Program.objects.create(
            title='Other Show', source='tvmaze', external_id='other-show',
        )
        self._airing(favorite_channel, favorite_program, timedelta(minutes=-5), timedelta(minutes=25), 'my-airing')
        self._airing(other_channel, other_program, timedelta(minutes=-5), timedelta(minutes=25), 'other-airing')

        user = get_user_model().objects.create_user(username='filter-viewer', password='password')
        other_user = get_user_model().objects.create_user(username='other-viewer', password='password')
        ChannelFavorite.objects.create(user=user, channel=favorite_channel)
        ChannelFavorite.objects.create(user=other_user, channel=other_channel)
        self.client.force_login(user)

        response = self.client.get(reverse('live_tv_guide'), {'favorites': '1'})

        self.assertContains(response, 'My Network')
        self.assertContains(response, 'My Show')
        self.assertNotContains(response, 'Other Network')
        self.assertNotContains(response, 'Other Show')
        self.assertContains(response, 'Show all channels')

    def test_category_filter_uses_normalized_channel_categories(self):
        drama_channel = Channel.objects.create(
            name='Drama Network', slug='drama-filter-network', region='US',
            source='tvmaze', external_id='drama-filter-network', categories=['Drama', 'Crime'],
        )
        comedy_channel = Channel.objects.create(
            name='Comedy Network', slug='comedy-filter-network', region='US',
            source='tvmaze', external_id='comedy-filter-network', categories=['Comedy'],
        )
        drama_program = Program.objects.create(
            title='Drama Program', source='tvmaze', external_id='drama-filter-program',
        )
        comedy_program = Program.objects.create(
            title='Comedy Program', source='tvmaze', external_id='comedy-filter-program',
        )
        self._airing(
            drama_channel, drama_program, timedelta(minutes=-5), timedelta(minutes=25),
            'drama-filter-airing',
        )
        self._airing(
            comedy_channel, comedy_program, timedelta(minutes=-5), timedelta(minutes=25),
            'comedy-filter-airing',
        )

        response = self.client.get(reverse('live_tv_guide'), {'category': 'Drama'})

        self.assertContains(response, 'Drama Network')
        self.assertContains(response, 'Drama Program')
        self.assertNotContains(response, 'Comedy Network')
        self.assertNotContains(response, 'Comedy Program')
        self.assertContains(response, '<option value="Drama" selected>', html=True)
        self.assertContains(response, '<option value="Comedy">Comedy</option>', html=True)

    def test_category_filter_combines_with_search(self):
        crime_channel = Channel.objects.create(
            name='Crime Network', slug='crime-category-network', region='US',
            source='tvmaze', external_id='crime-category-network', categories=['Drama'],
        )
        other_channel = Channel.objects.create(
            name='Other Drama', slug='other-drama-network', region='US',
            source='tvmaze', external_id='other-drama-network', categories=['Drama'],
        )
        crime_program = Program.objects.create(
            title='Crime Hour', source='tvmaze', external_id='crime-category-program',
        )
        other_program = Program.objects.create(
            title='Romance Hour', source='tvmaze', external_id='other-drama-program',
        )
        self._airing(
            crime_channel, crime_program, timedelta(minutes=-5), timedelta(minutes=25),
            'crime-category-airing',
        )
        self._airing(
            other_channel, other_program, timedelta(minutes=-5), timedelta(minutes=25),
            'other-drama-airing',
        )

        response = self.client.get(
            reverse('live_tv_guide'),
            {'category': 'Drama', 'q': 'Crime'},
        )

        self.assertContains(response, 'Crime Network')
        self.assertNotContains(response, 'Other Drama')
        self.assertContains(response, 'value="Crime"', html=False)

    def test_guide_search_matches_channel_name_and_keeps_now_next_context(self):
        channel = Channel.objects.create(
            name='Mystery Network', slug='mystery-network', region='US',
            source='tvmaze', external_id='mystery-network',
        )
        current = Program.objects.create(title='Morning Show', source='tvmaze', external_id='morning-show')
        upcoming = Program.objects.create(title='Evening Drama', source='tvmaze', external_id='evening-drama')
        self._airing(channel, current, timedelta(minutes=-5), timedelta(minutes=25), 'mystery-current')
        self._airing(channel, upcoming, timedelta(minutes=25), timedelta(minutes=85), 'mystery-next')

        response = self.client.get(reverse('live_tv_guide'), {'q': 'Mystery'})

        self.assertContains(response, 'Mystery Network')
        self.assertContains(response, 'Morning Show')
        self.assertContains(response, 'Evening Drama')
        self.assertContains(response, 'value="Mystery"', html=False)

    def test_guide_search_matches_upcoming_program_and_keeps_channel_context(self):
        channel = Channel.objects.create(
            name='Drama Network', slug='drama-network', region='US',
            source='tvmaze', external_id='drama-network',
        )
        current = Program.objects.create(title='Current Comedy', source='tvmaze', external_id='current-comedy')
        future = Program.objects.create(title='Crime Hour', source='tvmaze', external_id='crime-hour')
        self._airing(channel, current, timedelta(minutes=-10), timedelta(minutes=20), 'drama-current')
        self._airing(channel, future, timedelta(minutes=20), timedelta(minutes=80), 'drama-next')

        response = self.client.get(reverse('live_tv_guide'), {'q': 'Crime'})

        self.assertContains(response, 'Drama Network')
        self.assertContains(response, 'Current Comedy')
        self.assertContains(response, 'Crime Hour')

    def test_guide_search_matches_visible_later_program(self):
        channel = Channel.objects.create(
            name='Visible Search Network', slug='visible-search-network', region='US',
            source='tvmaze', external_id='visible-search-network',
        )
        current = Program.objects.create(
            title='Current Visible Show', source='tvmaze', external_id='current-visible-show',
        )
        next_program = Program.objects.create(
            title='Next Visible Show', source='tvmaze', external_id='next-visible-show',
        )
        later_program = Program.objects.create(
            title='Later Mystery Match', source='tvmaze', external_id='later-mystery-match',
        )
        self._airing(
            channel, current, timedelta(minutes=-5), timedelta(minutes=25),
            'visible-search-current',
        )
        self._airing(
            channel, next_program, timedelta(minutes=25), timedelta(minutes=55),
            'visible-search-next',
        )
        self._airing(
            channel, later_program, timedelta(minutes=55), timedelta(minutes=85),
            'visible-search-later',
        )

        response = self.client.get(reverse('live_tv_guide'), {'q': 'Mystery'})

        self.assertContains(response, 'Visible Search Network')
        self.assertContains(response, 'Later Mystery Match')

    def test_guide_search_does_not_match_hidden_future_program_beyond_later(self):
        channel = Channel.objects.create(
            name='Hidden Search Network', slug='hidden-search-network', region='US',
            source='tvmaze', external_id='hidden-search-network',
        )
        current = Program.objects.create(
            title='Current Plain Show', source='tvmaze', external_id='current-plain-show',
        )
        next_program = Program.objects.create(
            title='Next Plain Show', source='tvmaze', external_id='next-plain-show',
        )
        later_program = Program.objects.create(
            title='Later Plain Show', source='tvmaze', external_id='later-plain-show',
        )
        hidden_program = Program.objects.create(
            title='Hidden Mystery Match', source='tvmaze', external_id='hidden-mystery-match',
        )
        self._airing(
            channel, current, timedelta(minutes=-5), timedelta(minutes=25),
            'hidden-search-current',
        )
        self._airing(
            channel, next_program, timedelta(minutes=25), timedelta(minutes=55),
            'hidden-search-next',
        )
        self._airing(
            channel, later_program, timedelta(minutes=55), timedelta(minutes=85),
            'hidden-search-later',
        )
        self._airing(
            channel, hidden_program, timedelta(minutes=85), timedelta(minutes=115),
            'hidden-search-fourth',
        )

        response = self.client.get(reverse('live_tv_guide'), {'q': 'Mystery'})

        self.assertNotContains(response, 'Hidden Search Network')
        self.assertNotContains(response, 'Hidden Mystery Match')
        self.assertContains(response, 'No channels or visible Now / Next / Later programs match “Mystery” for US.')

    def test_guide_search_empty_state_is_specific(self):
        response = self.client.get(reverse('live_tv_guide'), {'q': 'Nothing Here'})

        self.assertContains(response, 'No channels or visible Now / Next / Later programs match “Nothing Here” for US.')

    def test_preferred_provider_ranks_playable_channel_destination(self):
        channel = Channel.objects.create(
            name='Ranked Network', slug='ranked-network', region='US',
            source='tvmaze', external_id='ranked-network',
        )
        program = Program.objects.create(title='Ranked Show', source='tvmaze', external_id='ranked-show')
        self._airing(channel, program, timedelta(minutes=-5), timedelta(minutes=25), 'ranked-airing')
        ChannelDestination.objects.create(
            channel=channel,
            provider='Other Provider',
            url='https://example.com/other',
            access_type='free',
            destination_type=ChannelDestination.DestinationType.DIRECT,
            source='fixture',
        )
        ChannelDestination.objects.create(
            channel=channel,
            provider='Prime Video',
            url='https://example.com/prime',
            access_type='subscription',
            destination_type=ChannelDestination.DestinationType.DIRECT,
            source='fixture',
        )
        user = get_user_model().objects.create_user(username='provider-viewer', password='password')
        DiscoveryPreference.objects.create(
            user=user,
            region='US',
            preferred_providers=['Amazon Prime Video'],
        )
        self.client.force_login(user)

        response = self.client.get(reverse('live_tv_guide'))

        self.assertContains(response, 'Prime Video · Subscription')
        self.assertContains(response, 'https://example.com/prime')
        self.assertNotContains(response, 'https://example.com/other')

    def test_favorite_toggle_preserves_search_and_favorites_filter(self):
        channel = Channel.objects.create(
            name='Search Favorite Network', slug='search-favorite-network', region='US',
            source='tvmaze', external_id='search-favorite-network',
        )
        user = get_user_model().objects.create_user(username='search-favorite-viewer', password='password')
        ChannelFavorite.objects.create(user=user, channel=channel)
        self.client.force_login(user)

        response = self.client.post(
            reverse('toggle_channel_favorite', args=[channel.pk]),
            {'favorites': '1', 'q': 'Crime Drama', 'category': 'Drama'},
        )

        self.assertRedirects(
            response,
            f"{reverse('live_tv_guide')}?favorites=1&q=Crime+Drama&category=Drama",
            fetch_redirect_response=False,
        )

    def test_favorites_filter_empty_state_is_truthful(self):
        user = get_user_model().objects.create_user(username='empty-favorites-viewer', password='password')
        self.client.force_login(user)

        response = self.client.get(reverse('live_tv_guide'), {'favorites': '1'})

        self.assertContains(response, 'No favorite channels currently have guide data for US.')
