from io import StringIO
from unittest.mock import call, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


class RefreshEpgCommandTests(SimpleTestCase):
    @patch('content.management.commands.refresh_epg.refresh_tvmaze_epg')
    def test_default_refreshes_us_region(self, refresh_tvmaze_epg):
        refresh_tvmaze_epg.return_value = 12
        output = StringIO()

        call_command('refresh_epg', stdout=output)

        refresh_tvmaze_epg.assert_called_once_with(country='US', retention_hours=6)
        self.assertIn('US: refreshed 12 airing(s).', output.getvalue())
        self.assertIn('Refreshed 12 airing(s) across 1 region(s).', output.getvalue())

    @patch('content.management.commands.refresh_epg.refresh_tvmaze_epg')
    def test_multiple_regions_are_normalized_and_deduplicated(self, refresh_tvmaze_epg):
        refresh_tvmaze_epg.side_effect = [4, 7]
        output = StringIO()

        call_command(
            'refresh_epg',
            regions=['us', 'CA', 'US'],
            retention_hours=2,
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
    def test_invalid_region_fails_before_refresh(self, refresh_tvmaze_epg):
        with self.assertRaisesMessage(CommandError, 'Invalid region'):
            call_command('refresh_epg', regions=['USA'])

        refresh_tvmaze_epg.assert_not_called()

    @patch('content.management.commands.refresh_epg.refresh_tvmaze_epg')
    def test_negative_retention_fails_before_refresh(self, refresh_tvmaze_epg):
        with self.assertRaisesMessage(CommandError, '--retention-hours must be zero or greater.'):
            call_command('refresh_epg', retention_hours=-1)

        refresh_tvmaze_epg.assert_not_called()
