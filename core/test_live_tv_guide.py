from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import Airing, AiringDestination, Channel, ChannelDestination, ChannelFavorite, DiscoveryPreference, Program


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

    def test_guide_search_empty_state_is_specific(self):
        response = self.client.get(reverse('live_tv_guide'), {'q': 'Nothing Here'})

        self.assertContains(response, 'No channels or upcoming programs match “Nothing Here” for US.')

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
            {'favorites': '1', 'q': 'Crime Drama'},
        )

        self.assertRedirects(
            response,
            f"{reverse('live_tv_guide')}?favorites=1&q=Crime+Drama",
            fetch_redirect_response=False,
        )

    def test_favorites_filter_empty_state_is_truthful(self):
        user = get_user_model().objects.create_user(username='empty-favorites-viewer', password='password')
        self.client.force_login(user)

        response = self.client.get(reverse('live_tv_guide'), {'favorites': '1'})

        self.assertContains(response, 'No favorite channels currently have guide data for US.')
