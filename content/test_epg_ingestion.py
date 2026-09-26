from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from content.models import Airing, AiringDestination, Channel, Program
from content.services import refresh_tvmaze_epg


class TvmazeEpgIngestionTests(TestCase):
    def _item(self, **overrides):
        values = {
            'schedule_external_id': 'episode-101',
            'channel_external_id': 'network-7',
            'external_id': 'show-42',
            'title': 'Example Show',
            'description': 'Episode metadata',
            'show_type': 'Scripted',
            'network': 'Example Network',
            'genres': ['Drama'],
            'airtime': '20:00',
            'runtime': 60,
        }
        values.update(overrides)
        return values

    @patch('content.services.fetch_live_tv_schedule')
    def test_refresh_creates_normalized_channel_program_and_airing(self, fetch_schedule):
        fetch_schedule.return_value = [self._item()]

        count = refresh_tvmaze_epg(country='US')

        self.assertEqual(count, 1)
        channel = Channel.objects.get()
        program = Program.objects.get()
        airing = Airing.objects.get()
        self.assertEqual((channel.source, channel.external_id, channel.region), ('tvmaze', 'network-7', 'US'))
        self.assertEqual(channel.name, 'Example Network')
        self.assertEqual(program.title, 'Example Show')
        self.assertEqual(airing.channel, channel)
        self.assertEqual(airing.program, program)
        self.assertGreater(airing.ends_at, airing.starts_at)

    @patch('content.services.fetch_live_tv_schedule')
    def test_refresh_persists_only_trusted_airing_destination(self, fetch_schedule):
        fetch_schedule.return_value = [self._item(
            watch_url='https://abc.com/episode/example',
            provider='ABC',
            access_type='other',
            watch_scope='episode',
        )]

        refresh_tvmaze_epg(country='US')

        destination = AiringDestination.objects.get()
        self.assertEqual(destination.provider, 'ABC')
        self.assertEqual(destination.scope, AiringDestination.Scope.EPISODE)
        self.assertEqual(destination.url, 'https://abc.com/episode/example')

    @patch('content.services.fetch_live_tv_schedule')
    def test_refresh_drops_untrusted_or_removed_airing_destination(self, fetch_schedule):
        fetch_schedule.return_value = [self._item(
            watch_url='https://abc.com/show/example',
            provider='ABC',
            access_type='other',
            watch_scope='show',
        )]
        refresh_tvmaze_epg(country='US')
        self.assertTrue(AiringDestination.objects.exists())

        fetch_schedule.return_value = [self._item(
            watch_url='https://untrusted.example/live',
            provider='Untrusted',
            access_type='free',
            watch_scope='show',
        )]
        refresh_tvmaze_epg(country='US')

        self.assertFalse(AiringDestination.objects.exists())

    @patch('content.services.fetch_live_tv_schedule')
    def test_refresh_is_idempotent_and_updates_existing_records(self, fetch_schedule):
        fetch_schedule.return_value = [self._item()]
        refresh_tvmaze_epg(country='US')
        fetch_schedule.return_value = [self._item(title='Updated Show', runtime=30)]

        refresh_tvmaze_epg(country='US')

        self.assertEqual(Channel.objects.count(), 1)
        self.assertEqual(Program.objects.count(), 1)
        self.assertEqual(Airing.objects.count(), 1)
        self.assertEqual(Program.objects.get().title, 'Updated Show')
        airing = Airing.objects.get()
        self.assertEqual(int((airing.ends_at - airing.starts_at).total_seconds() / 60), 30)

    @patch('content.services.fetch_live_tv_schedule')
    def test_refresh_skips_rows_without_stable_airing_or_channel_identity(self, fetch_schedule):
        fetch_schedule.return_value = [
            self._item(schedule_external_id=''),
            self._item(channel_external_id=''),
        ]

        self.assertEqual(refresh_tvmaze_epg(country='US'), 0)
        self.assertFalse(Airing.objects.exists())

    @patch('content.services.fetch_live_tv_schedule')
    def test_refresh_removes_only_expired_tvmaze_airings(self, fetch_schedule):
        fetch_schedule.return_value = []
        channel = Channel.objects.create(name='Old', slug='old', region='US', source='other', external_id='c1')
        program = Program.objects.create(title='Old', source='other', external_id='p1')
        old_end = timezone.now() - timezone.timedelta(hours=8)
        Airing.objects.create(
            channel=channel, program=program, starts_at=old_end - timezone.timedelta(hours=1),
            ends_at=old_end, source='other', external_id='a1',
        )
        tv_channel = Channel.objects.create(name='TVmaze', slug='tvmaze', region='US', source='tvmaze', external_id='c2')
        tv_program = Program.objects.create(title='TVmaze', source='tvmaze', external_id='p2')
        Airing.objects.create(
            channel=tv_channel, program=tv_program, starts_at=old_end - timezone.timedelta(hours=1),
            ends_at=old_end, source='tvmaze', external_id='a2',
        )

        refresh_tvmaze_epg(country='US', retention_hours=6)

        self.assertTrue(Airing.objects.filter(source='other').exists())
        self.assertFalse(Airing.objects.filter(source='tvmaze').exists())
