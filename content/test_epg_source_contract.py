from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from content.epg_sources import ScheduleNormalizationError, TvmazeScheduleAdapter
from content.models import Airing, Channel, Program
from content.services import refresh_epg_source


class FixtureScheduleAdapter:
    source = 'fixture'

    def __init__(self, rows, *, complete_snapshot=False):
        self.rows = rows
        self.calls = []
        self.complete_snapshot = complete_snapshot

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
            self._row(starts_at='2026-09-23T20:00:00', ends_at='2026-09-23T21:00:00'),
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

    def test_complete_snapshot_requests_unbounded_source_fetch(self):
        adapter = FixtureScheduleAdapter([], complete_snapshot=True)

        refresh_epg_source(adapter, region='US')

        self.assertEqual(adapter.calls, [('US', None)])

    def test_complete_snapshot_removes_missing_current_and_future_airings_for_region(self):
        now = timezone.now()
        channel = Channel.objects.create(
            name='Fixture Current', slug='fixture-current', region='US',
            source='fixture', external_id='channel-current',
        )
        program = Program.objects.create(
            title='Fixture Current', source='fixture', external_id='program-current',
        )
        Airing.objects.create(
            channel=channel,
            program=program,
            starts_at=now - timedelta(minutes=10),
            ends_at=now + timedelta(minutes=50),
            source='fixture',
            external_id='airing-current',
        )
        future_channel = Channel.objects.create(
            name='Fixture Future', slug='fixture-future', region='US',
            source='fixture', external_id='channel-future',
        )
        future_program = Program.objects.create(
            title='Fixture Future', source='fixture', external_id='program-future',
        )
        Airing.objects.create(
            channel=future_channel,
            program=future_program,
            starts_at=now + timedelta(hours=1),
            ends_at=now + timedelta(hours=2),
            source='fixture',
            external_id='airing-future',
        )

        refresh_epg_source(
            FixtureScheduleAdapter([], complete_snapshot=True),
            region='US',
            retention_hours=6,
        )

        self.assertFalse(Airing.objects.filter(source='fixture', channel__region='US').exists())

    def test_complete_snapshot_reconciliation_is_scoped_by_region_and_source(self):
        now = timezone.now()
        ca_channel = Channel.objects.create(
            name='CA Fixture', slug='ca-fixture', region='CA',
            source='fixture', external_id='ca-channel',
        )
        ca_program = Program.objects.create(
            title='CA Fixture', source='fixture', external_id='ca-program',
        )
        Airing.objects.create(
            channel=ca_channel,
            program=ca_program,
            starts_at=now,
            ends_at=now + timedelta(hours=1),
            source='fixture',
            external_id='ca-airing',
        )
        other_channel = Channel.objects.create(
            name='Other Source', slug='other-source', region='US',
            source='other', external_id='other-channel',
        )
        other_program = Program.objects.create(
            title='Other Source', source='other', external_id='other-program',
        )
        Airing.objects.create(
            channel=other_channel,
            program=other_program,
            starts_at=now,
            ends_at=now + timedelta(hours=1),
            source='other',
            external_id='other-airing',
        )

        refresh_epg_source(
            FixtureScheduleAdapter([], complete_snapshot=True),
            region='US',
            retention_hours=6,
        )

        self.assertTrue(Airing.objects.filter(source='fixture', channel__region='CA').exists())
        self.assertTrue(Airing.objects.filter(source='other', channel__region='US').exists())

    def test_complete_snapshot_preserves_recent_expired_airings_until_retention(self):
        now = timezone.now()
        channel = Channel.objects.create(
            name='Recent Fixture', slug='recent-fixture', region='US',
            source='fixture', external_id='recent-channel',
        )
        program = Program.objects.create(
            title='Recent Fixture', source='fixture', external_id='recent-program',
        )
        Airing.objects.create(
            channel=channel,
            program=program,
            starts_at=now - timedelta(hours=2),
            ends_at=now - timedelta(hours=1),
            source='fixture',
            external_id='recent-airing',
        )

        refresh_epg_source(
            FixtureScheduleAdapter([], complete_snapshot=True),
            region='US',
            retention_hours=6,
        )

        self.assertTrue(Airing.objects.filter(source='fixture', external_id='recent-airing').exists())

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
                'airstamp': '2026-09-26T20:30:00-04:00',
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

    def test_tvmaze_airstamp_preserves_date_and_timezone_across_midnight(self):
        def fetch_schedule(*, limit, country):
            return [{
                'schedule_external_id': 'late-episode',
                'channel_external_id': 'network',
                'external_id': 'show',
                'airtime': '00:35',
                'airstamp': '2026-09-27T00:35:00-04:00',
                'runtime': 60,
            }]

        rows = TvmazeScheduleAdapter(fetch_schedule=fetch_schedule).fetch_airings(region='US')

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['starts_at'].isoformat(), '2026-09-27T00:35:00-04:00')
        self.assertEqual(rows[0]['ends_at'].isoformat(), '2026-09-27T01:35:00-04:00')

    def test_tvmaze_adapter_rejects_snapshot_with_only_invalid_airstamps(self):
        def fetch_schedule(*, limit, country):
            return [
                {'airstamp': '', 'airtime': '20:00'},
                {'airstamp': '2026-09-26T20:00:00', 'airtime': '20:00'},
                {'airstamp': 'not-a-date', 'airtime': '20:00'},
            ]

        with self.assertRaises(ScheduleNormalizationError):
            TvmazeScheduleAdapter(fetch_schedule=fetch_schedule).fetch_airings(region='US')

    def test_tvmaze_nonempty_snapshot_with_no_normalizable_rows_fails_closed(self):
        def fetch_schedule(*, limit, country):
            return [
                {
                    'schedule_external_id': 'broken-1',
                    'channel_external_id': 'network',
                    'external_id': 'show',
                    'airstamp': '',
                },
                {
                    'schedule_external_id': 'broken-2',
                    'channel_external_id': 'network',
                    'external_id': 'show',
                    'airstamp': 'not-a-date',
                },
            ]

        adapter = TvmazeScheduleAdapter(fetch_schedule=fetch_schedule)

        with self.assertRaises(ScheduleNormalizationError):
            adapter.fetch_airings(region='US', limit=None)

    def test_tvmaze_partial_malformed_snapshot_fails_closed(self):
        def fetch_schedule(*, limit, country):
            return [
                {
                    'schedule_external_id': 'good-1',
                    'channel_external_id': 'network',
                    'external_id': 'show',
                    'airstamp': '2026-10-03T20:00:00-04:00',
                    'runtime': 60,
                },
                {
                    'schedule_external_id': 'bad-1',
                    'channel_external_id': 'network',
                    'external_id': 'show',
                    'airstamp': 'not-a-date',
                    'runtime': 60,
                },
            ]

        adapter = TvmazeScheduleAdapter(fetch_schedule=fetch_schedule)

        with self.assertRaises(ScheduleNormalizationError):
            adapter.fetch_airings(region='US', limit=None)

    def test_tvmaze_complete_snapshot_rejects_missing_stable_identity(self):
        def fetch_schedule(*, limit, country):
            return [
                {
                    'schedule_external_id': '',
                    'channel_external_id': 'network',
                    'external_id': 'show',
                    'airstamp': '2026-10-03T20:00:00-04:00',
                    'runtime': 60,
                },
                {
                    'schedule_external_id': 'episode-2',
                    'channel_external_id': '',
                    'external_id': 'show',
                    'airstamp': '2026-10-03T21:00:00-04:00',
                    'runtime': 60,
                },
                {
                    'schedule_external_id': 'episode-3',
                    'channel_external_id': 'network',
                    'external_id': '',
                    'airstamp': '2026-10-03T22:00:00-04:00',
                    'runtime': 60,
                },
            ]

        adapter = TvmazeScheduleAdapter(fetch_schedule=fetch_schedule)

        with self.assertRaises(ScheduleNormalizationError):
            adapter.fetch_airings(region='US', limit=None)

    def test_tvmaze_complete_snapshot_rejects_conflicting_duplicate_airing_identity(self):
        def fetch_schedule(*, limit, country):
            return [
                {
                    'schedule_external_id': 'episode-77',
                    'channel_external_id': 'network-a',
                    'external_id': 'show-a',
                    'airstamp': '2026-10-04T20:00:00-04:00',
                    'runtime': 60,
                },
                {
                    'schedule_external_id': 'episode-77',
                    'channel_external_id': 'network-b',
                    'external_id': 'show-b',
                    'airstamp': '2026-10-04T20:00:00-04:00',
                    'runtime': 60,
                },
            ]

        adapter = TvmazeScheduleAdapter(fetch_schedule=fetch_schedule)

        with self.assertRaises(ScheduleNormalizationError):
            adapter.fetch_airings(region='US', limit=None)

    def test_tvmaze_complete_snapshot_allows_duplicate_airing_with_same_identity(self):
        def fetch_schedule(*, limit, country):
            return [
                {
                    'schedule_external_id': 'episode-78',
                    'channel_external_id': 'network-a',
                    'external_id': 'show-a',
                    'airstamp': '2026-10-04T20:00:00-04:00',
                    'runtime': 60,
                },
                {
                    'schedule_external_id': 'episode-78',
                    'channel_external_id': 'network-a',
                    'external_id': 'show-a',
                    'airstamp': '2026-10-04T20:00:00-04:00',
                    'runtime': 60,
                },
            ]

        rows = TvmazeScheduleAdapter(fetch_schedule=fetch_schedule).fetch_airings(region='US', limit=None)

        self.assertEqual(len(rows), 1)

    def test_tvmaze_complete_snapshot_rejects_duplicate_airing_with_conflicting_time(self):
        def fetch_schedule(*, limit, country):
            return [
                {
                    'schedule_external_id': 'episode-79',
                    'channel_external_id': 'network-a',
                    'external_id': 'show-a',
                    'airstamp': '2026-10-04T20:00:00-04:00',
                    'runtime': 60,
                },
                {
                    'schedule_external_id': 'episode-79',
                    'channel_external_id': 'network-a',
                    'external_id': 'show-a',
                    'airstamp': '2026-10-04T21:00:00-04:00',
                    'runtime': 60,
                },
            ]

        adapter = TvmazeScheduleAdapter(fetch_schedule=fetch_schedule)

        with self.assertRaises(ScheduleNormalizationError):
            adapter.fetch_airings(region='US', limit=None)

    def test_tvmaze_legitimate_empty_snapshot_remains_valid(self):
        adapter = TvmazeScheduleAdapter(fetch_schedule=lambda **kwargs: [])

        rows = adapter.fetch_airings(region='US', limit=None)

        self.assertEqual(rows, [])

    def test_tvmaze_partial_invalid_timing_rejects_complete_snapshot(self):
        def fetch_schedule(*, limit, country):
            return [
                {'schedule_external_id': 'bad-time', 'airtime': 'not-a-time', 'airstamp': 'bad-time'},
                {
                    'schedule_external_id': 'good-time',
                    'channel_external_id': 'network',
                    'external_id': 'show',
                    'airtime': '10:00',
                    'airstamp': '2026-09-26T10:00:00+02:00',
                    'runtime': 0,
                },
            ]

        with self.assertRaises(ScheduleNormalizationError):
            TvmazeScheduleAdapter(fetch_schedule=fetch_schedule).fetch_airings(region='US')

    def test_tvmaze_adapter_defaults_nonpositive_runtime_for_valid_snapshot(self):
        def fetch_schedule(*, limit, country):
            return [{
                'schedule_external_id': 'good-time',
                'channel_external_id': 'network',
                'external_id': 'show',
                'airtime': '10:00',
                'airstamp': '2026-09-26T10:00:00+02:00',
                'runtime': 0,
            }]

        rows = TvmazeScheduleAdapter(fetch_schedule=fetch_schedule).fetch_airings(region='US')

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['airing_external_id'], 'good-time')
        self.assertEqual(int((rows[0]['ends_at'] - rows[0]['starts_at']).total_seconds() / 60), 30)
