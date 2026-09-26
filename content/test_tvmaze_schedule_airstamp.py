from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from content.services import fetch_live_tv_schedule


class TvmazeScheduleAirstampTests(SimpleTestCase):
    @patch('content.services.requests.get')
    def test_schedule_preserves_source_airstamp_for_epg_normalization(self, get):
        response = Mock()
        response.json.return_value = [{
            'id': 42,
            'airtime': '00:35',
            'airstamp': '2026-09-27T00:35:00-04:00',
            'runtime': 55,
            'show': {
                'id': 24,
                'name': 'Example Show',
                'network': {'id': 7, 'name': 'Example Network'},
            },
        }]
        get.return_value = response

        rows = fetch_live_tv_schedule(limit=10, country='US')

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['airtime'], '00:35')
        self.assertEqual(rows[0]['airstamp'], '2026-09-27T00:35:00-04:00')
        get.assert_called_once()
