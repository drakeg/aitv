from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from content.services import fetch_live_tv_schedule


class TvmazeScheduleCoverageTests(SimpleTestCase):
    @patch('content.services.requests.get')
    def test_schedule_keeps_show_without_official_site(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [{
            'season': 2,
            'number': 4,
            'airtime': '21:00',
            'runtime': 44,
            'show': {
                'id': 77,
                'name': 'Network Drama',
                'url': 'https://www.tvmaze.com/shows/77/network-drama',
                'officialSite': None,
                'type': 'Scripted',
                'genres': ['Drama', 'Crime'],
                'premiered': '2025-01-15',
                'network': {'name': 'Example Network'},
                'rating': {'average': 7.8},
                'image': {'medium': 'https://example.com/poster.jpg'},
                'summary': '<p>A real scheduled show.</p>',
            },
        }]
        mock_get.return_value = response

        items = fetch_live_tv_schedule(country='US')

        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item['title'], 'Network Drama')
        self.assertEqual(item['network'], 'Example Network')
        self.assertEqual(item['episode_label'], 'S2 E4')
        self.assertEqual(item['runtime'], 44)
        self.assertEqual(item['airtime'], '21:00')
        self.assertFalse(item['has_direct_watch'])
        self.assertEqual(item['watch_url'], '')
        self.assertEqual(item['url'], 'https://www.tvmaze.com/shows/77/network-drama')
        self.assertEqual(item['details_url'], 'https://www.tvmaze.com/shows/77/network-drama')
        self.assertEqual(item['action_label'], '')

    @patch('content.services.requests.get')
    def test_schedule_preserves_direct_provider_action_when_official_site_exists(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [{
            'season': 1,
            'number': 2,
            'airtime': '20:00',
            'runtime': 60,
            'show': {
                'id': 88,
                'name': 'Provider Show',
                'url': 'https://www.tvmaze.com/shows/88/provider-show',
                'officialSite': 'https://www.cbs.com/shows/provider-show/',
                'type': 'Scripted',
                'genres': ['Drama'],
                'network': {'name': 'CBS'},
                'rating': {'average': 8.0},
            },
        }]
        mock_get.return_value = response

        item = fetch_live_tv_schedule(country='US')[0]

        self.assertTrue(item['has_direct_watch'])
        self.assertEqual(item['watch_url'], 'https://www.cbs.com/shows/provider-show/')
        self.assertEqual(item['provider'], 'CBS')
        self.assertIn('CBS', item['action_label'])
