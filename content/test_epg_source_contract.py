from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from content.epg_sources import TvmazeScheduleAdapter
from content.models import Airing, Channel, Program
from content.services import refresh_epg_source


class FixtureScheduleAdapter:
    source = 'fixture'

    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def fetch_airings(self, *, region, limit=1000):
        self.calls.append((region, limit))
        return self.rows


class EpgSourceAdapterContractTests(TestCase):
    def _row(self, **overrides):
        starts_at = timezone.now() + timedelta(minutes=5)
        values = {
            'airing_external_id': 'airing-1',
            'channel_external_id': 'channel-1',
            'program_external_id': 'program-1',
            'channel_name': 'Fixture Network',
            'channel_categories': ['Drama'],
            'program_title': 'Fixture Show',
            'program_description': 'Fixture description',
            'program_type': 'Scripted',
            'starts_at': starts_at,
            'ends_at': starts_at + timedelta(minutes=60),
        }
        values.update(overrides)
        return values

    def test_generic_refresh_persists_adapter_provenance_and_region(self):
        adapter = FixtureScheduleAdapter([self._row()])

        count = refresh_epg_source(adapter, region='ca')

        self.assertEqual(count, 1)
        self.assertEqual(adapter.calls, [('CA', 1000)])
        channel = Channel.objects.get()
        program = Program.objects.get()
        airing = Airing.objects.get()
        self.assertEqual((channel.source, channel.region), ('fixture', 'CA'))
        self.assertEqual(program.source, 'fixture')
        self.assertEqual(airing.source, 'fixture')
        self.assertEqual(channel.slug, 'fixture-channel-1')

    def test_generic_refresh_rejects_incomplete_or_invalid_rows(self):
        starts_at = timezone.now()
        adapter = FixtureScheduleAdapter([
            self._row(airing_external_id=''),
            self._row(channel_external_id=''),
            self._row(program_external_id=''),
            self._row(ends_at=starts_at, starts_at=starts_at),
        ])

        self.assertEqual(refresh_epg_source(adapter), 0)
        self.assertFalse(Airing.objects.exists())

    def test_cleanup_is_scoped_to_the_adapter_source(self):
        old_end = timezone.now() - timedelta(hours=8)
        foreign_channel = Channel.objects.create(
            name='Foreign', slug='foreign', region='US', source='other', external_id='channel',
        )
        foreign_program = Program.objects.create(
            title='Foreign', source='other', external_id='program',
        )
        Airing.objects.create(
            channel=foreign_channel, program=foreign_program,
            starts_at=old_end - timedelta(hours=1), ends_at=old_end,
            source='other', external_id='airing',
        )
        own_channel = Channel.objects.create(
            name='Fixture', slug='fixture', region='US', source='fixture', external_id='channel',
        )
        own_program = Program.objects.create(
            title='Fixture', source='fixture', external_id='program',
        )
        Airing.objects.create(
            channel=own_channel, program=own_program,
            starts_at=old_end - timedelta(hours=1), ends_at=old_end,
            source='fixture', external_id='airing',
        )

        refresh_epg_source(FixtureScheduleAdapter([]), retention_hours=6)

        self.assertTrue(Airing.objects.filter(source='other').exists())
        self.assertFalse(Airing.objects.filter(source='fixture').exists())

    def test_tvmaze_adapter_normalizes_source_specific_schedule_shape(self):
        def fetch_schedule(*, limit, country):
            self.assertEqual((limit, country), (25, 'US'))
            return [{
                'schedule_external_id': 'episode-10',
                'channel_external_id': 'network-2',
                'external_id': 'show-3',
                'network': 'Example Network',
                'genres': ['Comedy'],
                'title': 'Example Show',
                'description': 'Description',
                'show_type': 'Scripted',
                'airtime': '20:30',
                'runtime': 45,
            }]

        rows = TvmazeScheduleAdapter(fetch_schedule=fetch_schedule).fetch_airings(region='US', limit=25)

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['airing_external_id'], 'episode-10')
        self.assertEqual(row['channel_external_id'], 'network-2')
        self.assertEqual(row['program_external_id'], 'show-3')
        self.assertEqual(row['channel_name'], 'Example Network')
        self.assertEqual(int((row['ends_at'] - row['starts_at']).total_seconds() / 60), 45)

    def test_tvmaze_adapter_skips_bad_airtime_and_defaults_bad_runtime(self):
        def fetch_schedule(*, limit, country):
            return [
                {'schedule_external_id': 'bad-time', 'airtime': 'not-a-time'},
                {
                    'schedule_external_id': 'good-time',
                    'channel_external_id': 'network',
                    'external_id': 'show',
                    'airtime': '10:00',
                    'runtime': 0,
                },
            ]

        rows = TvmazeScheduleAdapter(fetch_schedule=fetch_schedule).fetch_airings(region='US')

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['airing_external_id'], 'good-time')
        self.assertEqual(int((rows[0]['ends_at'] - rows[0]['starts_at']).total_seconds() / 60), 30)
