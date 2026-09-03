import os
from unittest.mock import Mock, patch

import requests
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from content.forms import QuickAddForm, extract_youtube_video_id
from content.models import ContentAvailability, ContentItem
from content.providers import detect_provider
from content.services import fetch_tmdb_watch_context, fetch_trending_movies, fetch_trending_tv
from watchlist.models import Watchlist


class TrendingContentServiceTests(SimpleTestCase):
    @patch.dict(os.environ, {}, clear=True)
    @patch('content.services.requests.get')
    def test_missing_tmdb_credentials_skip_request(self, mock_get):
        self.assertEqual(fetch_trending_movies(), [])
        self.assertEqual(fetch_trending_tv(), [])
        mock_get.assert_not_called()

    @patch.dict(os.environ, {'TMDB_READ_ACCESS_TOKEN': 'read-token', 'TMDB_API_KEY': 'query-key'}, clear=True)
    @patch('content.services.requests.get')
    def test_read_access_token_is_preferred(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {'results': []}
        mock_get.return_value = response

        fetch_trending_movies()

        mock_get.assert_called_once_with(
            'https://api.themoviedb.org/3/trending/movie/week',
            headers={'Authorization': 'Bearer read-token', 'accept': 'application/json'},
            timeout=5.0,
        )

    @patch.dict(os.environ, {'TMDB_API_KEY': 'test-key', 'TMDB_TIMEOUT_SECONDS': '3'}, clear=True)
    @patch('content.services.requests.get')
    def test_trending_movies_are_normalized_with_metadata(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {'results': [{'id': 42, 'title': 'Example Movie', 'poster_path': '/poster.jpg', 'overview': 'A useful example.', 'release_date': '2026-08-01', 'vote_average': 8.27}]}
        mock_get.return_value = response

        movies = fetch_trending_movies()

        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]['id'], 'tmdb_movie_42')
        self.assertEqual(movies[0]['content_type'], 'movie')
        self.assertEqual(movies[0]['release_year'], 2026)
        self.assertEqual(movies[0]['rating'], 8.3)
        self.assertEqual(movies[0]['external_source'], 'tmdb')
        self.assertTrue(movies[0]['is_external'])
        mock_get.assert_called_once_with(
            'https://api.themoviedb.org/3/trending/movie/week',
            params={'api_key': 'test-key'},
            timeout=3.0,
        )

    @patch.dict(os.environ, {'TMDB_API_KEY': 'test-key'}, clear=True)
    @patch('content.services.requests.get')
    def test_trending_tv_uses_name_and_first_air_date(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {'results': [{'id': 7, 'name': 'Example Series', 'first_air_date': '2024-02-20', 'vote_average': 7.5}]}
        mock_get.return_value = response

        shows = fetch_trending_tv()

        self.assertEqual(shows[0]['title'], 'Example Series')
        self.assertEqual(shows[0]['content_type'], 'tv')
        self.assertEqual(shows[0]['release_year'], 2024)
        self.assertEqual(shows[0]['url'], 'https://www.themoviedb.org/tv/7')

    @patch.dict(os.environ, {'TMDB_API_KEY': 'test-key'}, clear=True)
    @patch('content.services.requests.get')
    def test_request_failure_returns_empty_list(self, mock_get):
        mock_get.side_effect = requests.RequestException('unavailable')
        self.assertEqual(fetch_trending_movies(), [])

    @patch.dict(os.environ, {'TMDB_API_KEY': 'test-key', 'TMDB_TIMEOUT_SECONDS': 'invalid'}, clear=True)
    def test_invalid_timeout_returns_empty_list(self):
        self.assertEqual(fetch_trending_movies(), [])

    @patch.dict(os.environ, {'TMDB_API_KEY': 'test-key'}, clear=True)
    @patch('content.services.requests.get')
    def test_watch_context_keeps_provider_list_compact(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            'runtime': 111,
            'watch/providers': {
                'results': {
                    'US': {
                        'link': 'https://www.themoviedb.org/movie/42/watch',
                        'free': [{'provider_name': 'Free One'}],
                        'ads': [{'provider_name': 'Ads Two'}],
                        'flatrate': [{'provider_name': 'Subscription Three'}],
                        'rent': [{'provider_name': 'Rent Four'}],
                    }
                }
            },
        }
        mock_get.return_value = response

        context = fetch_tmdb_watch_context('movie', '42')

        self.assertEqual(len(context['providers']), 2)
        self.assertEqual(context['provider_count'], 4)
        self.assertEqual(context['additional_provider_count'], 2)
        self.assertEqual(context['runtime'], 111)


class YouTubeParsingTests(SimpleTestCase):
    def test_supported_youtube_urls(self):
        video_id = 'dQw4w9WgXcQ'
        urls = [
            f'https://www.youtube.com/watch?v={video_id}&feature=share',
            f'https://youtu.be/{video_id}?si=abc123',
            f'https://www.youtube.com/shorts/{video_id}?feature=share',
            f'https://www.youtube.com/embed/{video_id}',
            f'https://m.youtube.com/watch?v={video_id}',
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(extract_youtube_video_id(url), video_id)

    def test_non_youtube_spoofed_and_invalid_ids_are_rejected(self):
        self.assertIsNone(extract_youtube_video_id('https://example.com/watch?v=dQw4w9WgXcQ'))
        self.assertIsNone(extract_youtube_video_id('https://youtube.com.example.com/watch?v=dQw4w9WgXcQ'))
        self.assertIsNone(extract_youtube_video_id('https://youtube.com/watch?v=invalid!id!'))

    def test_quick_add_sets_youtube_metadata_and_video_type(self):
        form = QuickAddForm(data={'title': 'Example', 'url': 'https://youtu.be/dQw4w9WgXcQ?si=test', 'genre': 'Music', 'content_type': 'movie'})
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save(commit=False)
        self.assertEqual(item.source_type, 'youtube')
        self.assertEqual(item.content_type, 'video')
        self.assertEqual(item.thumbnail, 'https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg')

    def test_manual_non_youtube_content_preserves_selected_type(self):
        form = QuickAddForm(data={'title': 'Example Series', 'url': 'https://example.com/series', 'genre': 'Drama', 'content_type': 'tv'})
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save(commit=False)
        self.assertEqual(item.source_type, 'manual')
        self.assertEqual(item.content_type, 'tv')


class ProviderDetectionTests(SimpleTestCase):
    def test_network_and_streaming_hosts_are_recognized(self):
        cases = {
            'https://www.abc.com/shows/example': 'ABC',
            'https://www.cbs.com/shows/survivor/': 'CBS',
            'https://www.nbc.com/example': 'NBC',
            'https://www.fox.com/example': 'FOX',
            'https://www.pbs.org/show/frontline/': 'PBS',
            'https://www.cwtv.com/shows/example/': 'The CW',
            'https://tubitv.com/movies/example': 'Tubi',
            'https://www.netflix.com/title/example': 'Netflix',
        }
        for url, expected in cases.items():
            with self.subTest(url=url):
                self.assertEqual(detect_provider(url)['provider'], expected)

    def test_provider_spoofed_hosts_are_not_recognized(self):
        self.assertIsNone(detect_provider('https://cbs.com.example.com/shows/survivor'))
        self.assertIsNone(detect_provider('https://example.com/?next=https://pbs.org/show/frontline'))


class DirectProviderFormTests(TestCase):
    def test_direct_network_url_creates_availability(self):
        form = QuickAddForm(data={'title': 'Survivor', 'url': 'https://www.cbs.com/shows/survivor/', 'genre': 'Reality', 'content_type': 'tv'})
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save()
        self.assertEqual(item.source_type, 'network')
        availability = ContentAvailability.objects.get(content=item)
        self.assertEqual(availability.provider, 'CBS')
        self.assertEqual(availability.url, item.url)
        self.assertEqual(availability.action_label, 'Open CBS')

    def test_free_provider_uses_watch_action_label(self):
        form = QuickAddForm(data={'title': 'FRONTLINE', 'url': 'https://www.pbs.org/show/frontline/', 'genre': 'Documentary', 'content_type': 'tv'})
        self.assertTrue(form.is_valid(), form.errors)
        item = form.save()
        self.assertEqual(item.availabilities.get().action_label, 'Watch on PBS')


class ContentManagementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='test-password')
        self.item = ContentItem.objects.create(title='Managed Item', url='https://example.com/video', genre='Drama', source_type='manual', content_type='movie')

    def test_edit_requires_authentication(self):
        response = self.client.get(reverse('content:edit', args=[self.item.id]))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_edit_content_type(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('content:edit', args=[self.item.id]), {'title': 'Updated', 'url': 'https://example.com/updated', 'genre': 'Drama', 'content_type': 'tv'})
        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, 'Updated')
        self.assertEqual(self.item.content_type, 'tv')

    def test_delete_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('content:delete', args=[self.item.id]))
        self.assertEqual(response.status_code, 405)

    def test_tmdb_movie_card_save_imports_once_and_adds_to_watchlist(self):
        self.client.force_login(self.user)
        payload = {
            'title': 'Example Movie',
            'url': 'https://www.themoviedb.org/movie/42',
            'genre': 'Movie',
            'thumbnail': 'https://image.tmdb.org/t/p/w500/poster.jpg',
            'content_type': 'movie',
            'description': 'Example overview',
            'release_year': '2026',
            'rating': '8.4',
            'external_source': 'tmdb',
            'external_id': '42',
        }
        first = self.client.post(reverse('content:import_external'), payload)
        second = self.client.post(reverse('content:import_external'), payload)

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        matches = ContentItem.objects.filter(external_source='tmdb', external_id='42')
        self.assertEqual(matches.count(), 1)
        item = matches.get()
        self.assertEqual(item.content_type, 'movie')
        self.assertEqual(item.release_year, 2026)
        self.assertTrue(Watchlist.objects.filter(user=self.user, content=item).exists())
        self.assertEqual(Watchlist.objects.filter(user=self.user, content=item).count(), 1)

    def test_tmdb_tv_card_save_adds_to_watchlist(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('content:import_external'), {
            'title': 'Example Series',
            'url': 'https://www.themoviedb.org/tv/7',
            'genre': 'TV',
            'content_type': 'tv',
            'external_source': 'tmdb',
            'external_id': '7',
        })
        self.assertEqual(response.status_code, 302)
        item = ContentItem.objects.get(content_type='tv', external_id='7')
        self.assertTrue(Watchlist.objects.filter(user=self.user, content=item).exists())

    def test_external_import_rejects_missing_tmdb_identity(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('content:import_external'), {'title': 'Fake', 'url': 'https://www.themoviedb.org/movie/42', 'content_type': 'movie'})
        self.assertEqual(response.status_code, 400)
