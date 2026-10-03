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
    def test_home_discovery_deduplicates_repeated_show_airings(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        show = {
            'id': 501,
            'name': 'Repeated Show',
            'url': 'https://www.tvmaze.com/shows/501/repeated-show',
            'officialSite': None,
            'type': 'Scripted',
            'genres': ['Drama'],
            'network': {'id': 17, 'name': 'Example Network'},
            'rating': {'average': 7.0},
        }
        response.json.return_value = [
            {'id': 1001, 'season': 1, 'number': 1, 'airtime': '20:00', 'airstamp': '2026-10-01T20:00:00-04:00', 'runtime': 30, 'show': show},
            {'id': 1002, 'season': 1, 'number': 2, 'airtime': '20:30', 'airstamp': '2026-10-01T20:30:00-04:00', 'runtime': 30, 'show': show},
        ]
        mock_get.return_value = response

        items = fetch_live_tv_schedule(country='US')

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['schedule_external_id'], '1001')

    @patch('content.services.requests.get')
    def test_epg_fetch_mode_preserves_repeated_show_airings(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        show = {
            'id': 502,
            'name': 'Repeated EPG Show',
            'url': 'https://www.tvmaze.com/shows/502/repeated-epg-show',
            'officialSite': None,
            'type': 'Scripted',
            'genres': ['Drama'],
            'network': {'id': 18, 'name': 'EPG Network'},
            'rating': {'average': 7.0},
        }
        response.json.return_value = [
            {'id': 2001, 'season': 1, 'number': 1, 'airtime': '21:00', 'airstamp': '2026-10-01T21:00:00-04:00', 'runtime': 30, 'show': show},
            {'id': 2002, 'season': 1, 'number': 2, 'airtime': '21:30', 'airstamp': '2026-10-01T21:30:00-04:00', 'runtime': 30, 'show': show},
        ]
        mock_get.return_value = response

        items = fetch_live_tv_schedule(country='US', deduplicate_shows=False)

        self.assertEqual([item['schedule_external_id'] for item in items], ['2001', '2002'])

    @patch('content.services.requests.get')
    def test_unbounded_schedule_mode_does_not_truncate_results(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [
            {
                'id': episode_id,
                'season': 1,
                'number': episode_id,
                'airtime': '20:00',
                'airstamp': f'2026-10-0{episode_id}T20:00:00-04:00',
                'runtime': 30,
                'show': {
                    'id': 600 + episode_id,
                    'name': f'Show {episode_id}',
                    'url': f'https://www.tvmaze.com/shows/{600 + episode_id}/show-{episode_id}',
                    'officialSite': None,
                    'type': 'Scripted',
                    'genres': ['Drama'],
                    'network': {'id': 30 + episode_id, 'name': f'Network {episode_id}'},
                    'rating': {'average': 7.0},
                },
            }
            for episode_id in range(1, 4)
        ]
        mock_get.return_value = response

        limited = fetch_live_tv_schedule(limit=1, country='US', deduplicate_shows=False)
        unbounded = fetch_live_tv_schedule(limit=None, country='US', deduplicate_shows=False)

        self.assertEqual(len(limited), 1)
        self.assertEqual(len(unbounded), 3)

    @patch('content.services.requests.get')
    def test_unknown_official_site_is_details_only_not_direct_watch(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [{
            'season': 1, 'number': 3, 'airtime': '19:00', 'runtime': 30,
            'show': {
                'id': 81, 'name': 'Independent Show',
                'url': 'https://www.tvmaze.com/shows/81/independent-show',
                'officialSite': 'https://independent.example/shows/independent-show',
                'type': 'Scripted', 'genres': ['Comedy'],
                'network': {'name': 'Independent Network'},
                'rating': {'average': 7.0},
            },
        }]
        mock_get.return_value = response

        item = fetch_live_tv_schedule(country='US')[0]

        self.assertFalse(item['has_direct_watch'])
        self.assertEqual(item['watch_url'], '')
        self.assertEqual(item['url'], 'https://www.tvmaze.com/shows/81/independent-show')
        self.assertEqual(item['details_url'], 'https://independent.example/shows/independent-show')
        self.assertEqual(item['provider'], 'Independent Network')
        self.assertEqual(item['access_type'], '')
        self.assertEqual(item['action_label'], '')

    @patch('content.services.requests.get')
    def test_recognized_episode_url_is_preferred_over_show_homepage(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [{
            'season': 4, 'number': 7, 'airtime': '20:00', 'runtime': 42,
            'url': 'https://www.cbs.com/shows/provider-show/video/s4e7/',
            'show': {
                'id': 87, 'name': 'Provider Show',
                'url': 'https://www.tvmaze.com/shows/87/provider-show',
                'officialSite': 'https://www.cbs.com/shows/provider-show/',
                'type': 'Scripted', 'genres': ['Drama'],
                'network': {'name': 'CBS'}, 'rating': {'average': 8.0},
            },
        }]
        mock_get.return_value = response

        item = fetch_live_tv_schedule(country='US')[0]

        self.assertTrue(item['has_direct_watch'])
        self.assertEqual(item['watch_scope'], 'episode')
        self.assertEqual(item['watch_url'], 'https://www.cbs.com/shows/provider-show/video/s4e7/')
        self.assertEqual(item['details_url'], 'https://www.cbs.com/shows/provider-show/')
        self.assertEqual(item['provider'], 'CBS')

    @patch('content.services.requests.get')
    def test_unrecognized_episode_url_does_not_override_recognized_show_destination(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [{
            'season': 1, 'number': 2, 'airtime': '20:00', 'runtime': 60,
            'url': 'https://www.tvmaze.com/episodes/123/provider-show-1x02',
            'show': {
                'id': 89, 'name': 'Provider Show',
                'url': 'https://www.tvmaze.com/shows/89/provider-show',
                'officialSite': 'https://www.cbs.com/shows/provider-show/',
                'type': 'Scripted', 'genres': ['Drama'],
                'network': {'name': 'CBS'}, 'rating': {'average': 8.0},
            },
        }]
        mock_get.return_value = response

        item = fetch_live_tv_schedule(country='US')[0]

        self.assertEqual(item['watch_scope'], 'show')
        self.assertEqual(item['watch_url'], 'https://www.cbs.com/shows/provider-show/')

    @patch('content.services.requests.get')
    def test_network_article_official_site_is_not_promoted_to_direct_watch(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [{
            'season': 1, 'number': 1, 'airtime': '18:00', 'runtime': 30,
            'show': {
                'id': 90, 'name': 'Network News Special',
                'url': 'https://www.tvmaze.com/shows/90/network-news-special',
                'officialSite': 'https://www.cbs.com/news/example-story/',
                'type': 'News', 'genres': [],
                'network': {'name': 'CBS'}, 'rating': {'average': 6.5},
            },
        }]
        mock_get.return_value = response

        item = fetch_live_tv_schedule(country='US')[0]

        self.assertFalse(item['has_direct_watch'])
        self.assertEqual(item['watch_url'], '')
        self.assertEqual(item['url'], 'https://www.tvmaze.com/shows/90/network-news-special')
        self.assertEqual(item['details_url'], 'https://www.cbs.com/news/example-story/')

    @patch('content.services.requests.get')
    def test_pbs_non_watch_official_site_remains_details_only(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = [{
            'season': 1, 'number': 1, 'airtime': '20:00', 'runtime': 60,
            'show': {
                'id': 91, 'name': 'PBS Special',
                'url': 'https://www.tvmaze.com/shows/91/pbs-special',
                'officialSite': 'https://www.pbs.org/about/about-pbs/',
                'type': 'Documentary', 'genres': ['History'],
                'network': {'name': 'PBS'}, 'rating': {'average': 7.5},
            },
        }]
        mock_get.return_value = response

        item = fetch_live_tv_schedule(country='US')[0]

        self.assertFalse(item['has_direct_watch'])
        self.assertEqual(item['watch_url'], '')
        self.assertEqual(item['url'], 'https://www.tvmaze.com/shows/91/pbs-special')
        self.assertEqual(item['details_url'], 'https://www.pbs.org/about/about-pbs/')

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
        self.assertEqual(item['watch_scope'], 'show')
        self.assertIn('CBS', item['action_label'])
