from datetime import timedelta

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from content.models import Airing, Channel, Program


class LiveTvQueryEfficiencyTests(TestCase):
    def _airing(self, channel, program, start_delta, end_delta, external_id, *, schedule_date=None):
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

    def _channel_with_current_airing(self, index):
        channel = Channel.objects.create(
            name=f'Query Network {index:02d}',
            slug=f'query-network-{index:02d}',
            region='US',
            source='tvmaze',
            external_id=f'query-network-{index:02d}',
            categories=['Drama'],
        )
        program = Program.objects.create(
            title=f'Query Program {index:02d}',
            source='tvmaze',
            external_id=f'query-program-{index:02d}',
        )
        self._airing(
            channel,
            program,
            timedelta(minutes=-5),
            timedelta(minutes=25),
            f'query-airing-{index:02d}',
        )
        return channel

    def test_guide_query_count_is_bounded_as_channel_count_grows(self):
        self._channel_with_current_airing(1)
        with CaptureQueriesContext(connection) as one_channel_queries:
            response = self.client.get(reverse('live_tv_guide'))
        self.assertEqual(response.status_code, 200)

        for index in range(2, 12):
            self._channel_with_current_airing(index)

        with CaptureQueriesContext(connection) as many_channel_queries:
            response = self.client.get(reverse('live_tv_guide'))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(many_channel_queries), len(one_channel_queries))
        # Global operator branding contributes one fixed settings lookup; the
        # equality assertion above still protects against channel-count N+1 growth.
        self.assertLessEqual(len(many_channel_queries), 6)

    def test_schedule_day_counts_use_grouped_database_aggregation(self):
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        channel = Channel.objects.create(
            name='Counted Schedule Network',
            slug='counted-schedule-network',
            region='US',
            source='tvmaze',
            external_id='counted-schedule-network',
            categories=['Drama'],
        )
        program = Program.objects.create(
            title='Counted Schedule Program',
            source='tvmaze',
            external_id='counted-schedule-program',
        )
        for index in range(20):
            self._airing(
                channel,
                program,
                timedelta(minutes=index),
                timedelta(minutes=index + 30),
                f'counted-today-{index}',
                schedule_date=today,
            )
        for index in range(15):
            self._airing(
                channel,
                program,
                timedelta(days=1, minutes=index),
                timedelta(days=1, minutes=index + 30),
                f'counted-tomorrow-{index}',
                schedule_date=tomorrow,
            )

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(
                reverse('live_tv_channel_schedule', args=[channel.pk]),
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item['airing_count'] for item in response.context['schedule_days'][:2]],
            [20, 15],
        )
        aggregation_queries = [
            query['sql']
            for query in queries.captured_queries
            if 'COUNT(' in query['sql'].upper()
            and 'source_schedule_date' in query['sql']
        ]
        self.assertEqual(len(aggregation_queries), 1)
        self.assertIn('GROUP BY', aggregation_queries[0].upper())
        # Global operator branding contributes one fixed settings lookup while
        # schedule-day counts remain one grouped aggregation query.
        self.assertLessEqual(len(queries), 7)
