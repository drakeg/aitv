import os
from io import StringIO
from unittest.mock import Mock, patch

import requests
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from content.forms import QuickAddForm, extract_youtube_video_id
from content.models import ContentItem
from content.services import fetch_trending_movies


class TrendingMoviesServiceTests(SimpleTestCase):
    @patch.dict(os.environ, {}, clear=True)
    @patch('content.services.requests.get')
    def test_missing_api_key_skips_request(self, mock_get):
        self.assertEqual(fetch_trending_movies(), [])
        mock_get.assert_not_called()

    @patch.dict(
        os.environ,
        {'TMDB_API_KEY': 'test-key', 'TMDB_TIMEOUT_SECONDS': '3'},
        clear=True,
    )
    @patch('content.services.requests.get')
    def test_trending_movies_are_normalized(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            'results': [
                {
                    'id': 42,
                    'title': 'Example Movie',
                    'poster_path': '/poster.jpg',
                }
            ]
        }
        mock_get.return_value = response

        movies = fetch_trending_movies()

        self.assertEqual(len(movies), 1)
        self.assertEqual(movies[0]['id'], 'tmdb_42')
        self.assertEqual(movies[0]['title'], 'Example Movie')
        self.assertTrue(movies[0]['is_external'])
        mock_get.assert_called_once_with(
            'https://api.themoviedb.org/3/trending/movie/week',
            params={'api_key': 'test-key'},
            timeout=3.0,
        )

    @patch.dict(os.environ, {'TMDB_API_KEY': 'test-key'}, clear=True)
    @patch('content.services.requests.get')
    def test_request_failure_returns_empty_list(self, mock_get):
        mock_get.side_effect = requests.RequestException('unavailable')

        self.assertEqual(fetch_trending_movies(), [])

    @patch.dict(
        os.environ,
        {'TMDB_API_KEY': 'test-key', 'TMDB_TIMEOUT_SECONDS': 'invalid'},
        clear=True,
    )
    def test_invalid_timeout_returns_empty_list(self):
        self.assertEqual(fetch_trending_movies(), [])


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

    def test_non_youtube_and_spoofed_hosts_are_rejected(self):
        self.assertIsNone(extract_youtube_video_id('https://example.com/watch?v=dQw4w9WgXcQ'))
        self.assertIsNone(extract_youtube_video_id('https://youtube.com.example.com/watch?v=dQw4w9WgXcQ'))

    def test_quick_add_sets_youtube_metadata(self):
        form = QuickAddForm(data={
            'title': 'Example',
            'url': 'https://youtu.be/dQw4w9WgXcQ?si=test',
            'genre': 'Music',
        })

        self.assertTrue(form.is_valid(), form.errors)
        item = form.save(commit=False)
        self.assertEqual(item.source_type, 'youtube')
        self.assertEqual(
            item.thumbnail,
            'https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
        )


class DemoContentCommandTests(TestCase):
    def test_seed_demo_content_is_idempotent(self):
        output = StringIO()

        call_command('seed_demo_content', stdout=output)
        first_count = ContentItem.objects.count()
        call_command('seed_demo_content', stdout=output)

        self.assertEqual(first_count, 4)
        self.assertEqual(ContentItem.objects.count(), 4)
        self.assertEqual(ContentItem.objects.filter(source_type='youtube').count(), 4)
        self.assertTrue(ContentItem.objects.filter(genre__icontains='comedy').exists())
        self.assertTrue(ContentItem.objects.filter(genre__icontains='action').exists())


class ContentManagementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='tester',
            password='test-password',
        )
        self.item = ContentItem.objects.create(
            title='Managed Item',
            url='https://example.com/video',
            genre='Drama',
            source_type='movie',
        )

    def test_edit_requires_authentication(self):
        response = self.client.get(reverse('content:edit', args=[self.item.id]))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_edit_content(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('content:edit', args=[self.item.id]),
            {'title': 'Updated', 'url': 'https://example.com/updated', 'genre': 'Drama'},
        )

        self.assertEqual(response.status_code, 302)
        self.item.refresh_from_db()
        self.assertEqual(self.item.title, 'Updated')

    def test_delete_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('content:delete', args=[self.item.id]))
        self.assertEqual(response.status_code, 405)

    def test_tmdb_card_can_be_imported_once(self):
        self.client.force_login(self.user)
        payload = {
            'title': 'Example Movie',
            'url': 'https://www.themoviedb.org/movie/42',
            'genre': 'Movie',
            'thumbnail': 'https://image.tmdb.org/t/p/w500/poster.jpg',
        }

        first = self.client.post(reverse('content:import_external'), payload)
        second = self.client.post(reverse('content:import_external'), payload)

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(
            ContentItem.objects.filter(url='https://www.themoviedb.org/movie/42').count(),
            1,
        )
