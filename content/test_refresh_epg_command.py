from io import StringIO
from unittest.mock import call, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from content.models import EpgRefreshState


class RefreshEpgCommandTests(TestCase):
    @patch('content.management.commands.refresh_epg.refresh_tvmaze_epg')
    def test_default_refreshes_us_region(self, refresh_tvmaze_epg):
        refresh_tvmaze_epg.return_value = 12
        output = StringIO()

        call_command('refresh_epg', stdout=output)

        refresh_tvmaze_epg.assert_called_once_with(country='US', retention_hours=6)
        self.assertIn('US: refreshed 12 airing(s).', output.getvalue())
        self.assertIn('Refreshed 12 airing(s) across 1 region(s).', output.getvalue())
        state = EpgRefreshState.objects.get(source='tvmaze', region='US')
        self.assertEqual(state.airing_count, 12)
        self.assertEqual(state.status, EpgRefreshState.Status.SUCCESS)
        self.assertEqual(state.last_error, '')
        self.assertIsNotNone(state.attempted_at)

    @patch('content.management.commands.refresh_epg.refresh_tvmaze_epg')
    def test_multiple_regions_are_normalized_and_deduplicated(self, refresh_tvmaze_epg):
        refresh_tvmaze_epg.side_effect = [4, 7]
        output = StringIO()

        call_command(
            'refresh_epg',
            '--region', 'us',
            '--region', 'CA',
            '--region', 'US',
            '--retention-hours', '2',
            stdout=output,
        )

        self.assertEqual(
            refresh_tvmaze_epg.call_args_list,
            [
                call(country='US', retention_hours=2),
                call(country='CA', retention_hours=2),
            ],
        )
        self.assertIn('Refreshed 11 airing(s) across 2 region(s).', output.getvalue())
        self.assertEqual(
            set(EpgRefreshState.objects.values_list('region', 'airing_count')),
            {('US', 4), ('CA', 7)},
        )

    @patch('content.management.commands.refresh_epg.refresh_tvmaze_epg')
    def test_comma_separated_regions_support_worker_configuration(self, refresh_tvmaze_epg):
        refresh_tvmaze_epg.side_effect = [3, 5]
        output = StringIO()

        call_command('refresh_epg', regions_csv='US,ca', stdout=output)

        self.assertEqual(
            refresh_tvmaze_epg.call_args_list,
            [
                call(country='US', retention_hours=6),
                call(country='CA', retention_hours=6),
            ],
        )
        self.assertIn('Refreshed 8 airing(s) across 2 region(s).', output.getvalue())

    @patch('content.management.commands.refresh_epg.refresh_tvmaze_epg')
    def test_failure_is_recorded_without_erasing_last_success(self, refresh_tvmaze_epg):
        previous = EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            refreshed_at=timezone.now() - timezone.timedelta(hours=1),
            attempted_at=timezone.now() - timezone.timedelta(hours=1),
            airing_count=21,
            status=EpgRefreshState.Status.SUCCESS,
        )
        refresh_tvmaze_epg.side_effect = RuntimeError('upstream unavailable')

        with self.assertRaisesMessage(CommandError, 'EPG refresh failed for US'):
            call_command('refresh_epg')

        previous.refresh_from_db()
        self.assertEqual(previous.status, EpgRefreshState.Status.FAILURE)
        self.assertEqual(previous.airing_count, 21)
        self.assertIsNotNone(previous.refreshed_at)
        self.assertIn('RuntimeError: upstream unavailable', previous.last_error)

    @patch('content.management.commands.refresh_epg.refresh_tvmaze_epg')
    def test_multi_region_refresh_continues_after_one_failure(self, refresh_tvmaze_epg):
        refresh_tvmaze_epg.side_effect = [RuntimeError('US failed'), 7]

        with self.assertRaisesMessage(CommandError, 'EPG refresh failed for US'):
            call_command('refresh_epg', regions_csv='US,CA')

        us_state = EpgRefreshState.objects.get(source='tvmaze', region='US')
        ca_state = EpgRefreshState.objects.get(source='tvmaze', region='CA')
        self.assertEqual(us_state.status, EpgRefreshState.Status.FAILURE)
        self.assertEqual(ca_state.status, EpgRefreshState.Status.SUCCESS)
        self.assertEqual(ca_state.airing_count, 7)

    @patch('content.management.commands.refresh_epg.refresh_tvmaze_epg')
    def test_invalid_region_fails_before_refresh(self, refresh_tvmaze_epg):
        with self.assertRaisesMessage(CommandError, 'Invalid region'):
            call_command('refresh_epg', '--region', 'USA')

        refresh_tvmaze_epg.assert_not_called()

    @patch('content.management.commands.refresh_epg.refresh_tvmaze_epg')
    def test_negative_retention_fails_before_refresh(self, refresh_tvmaze_epg):
        with self.assertRaisesMessage(CommandError, '--retention-hours must be zero or greater.'):
            call_command('refresh_epg', retention_hours=-1)

        refresh_tvmaze_epg.assert_not_called()
