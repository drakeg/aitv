from unittest.mock import Mock, patch

import requests

from django.test import SimpleTestCase

from content.services import ScheduleFetchError, fetch_live_tv_schedule


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

    @patch('content.services.requests.get')
    def test_transport_failure_is_empty_for_home_but_raises_for_epg(self, get):
        get.side_effect = requests.Timeout('sensitive-url?token=secret')

        self.assertEqual(fetch_live_tv_schedule(country='US'), [])
        with self.assertRaisesMessage(ScheduleFetchError, 'TVmaze schedule request failed'):
            fetch_live_tv_schedule(country='US', strict=True)

    @patch('content.services.requests.get')
    def test_malformed_json_fails_only_strict_refresh(self, get):
        response = Mock()
        response.json.side_effect = ValueError('invalid JSON')
        get.return_value = response

        self.assertEqual(fetch_live_tv_schedule(), [])
        with self.assertRaisesMessage(ScheduleFetchError, 'TVmaze schedule request failed'):
            fetch_live_tv_schedule(strict=True)

    @patch('content.services.requests.get')
    def test_unexpected_payload_fails_strict_refresh(self, get):
        response = Mock()
        response.json.return_value = {'error': 'upstream failure'}
        get.return_value = response

        self.assertEqual(fetch_live_tv_schedule(), [])
        with self.assertRaisesMessage(ScheduleFetchError, 'TVmaze schedule response is not a list'):
            fetch_live_tv_schedule(strict=True)

    @patch('content.services.requests.get')
    def test_legitimate_empty_schedule_succeeds_in_strict_mode(self, get):
        response = Mock()
        response.json.return_value = []
        get.return_value = response

        self.assertEqual(fetch_live_tv_schedule(strict=True), [])
