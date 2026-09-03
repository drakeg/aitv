from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from content.models import DiscoveryPreference


class DiscoveryPreferenceTests(TestCase):
    def _item(self, title, genres, *, is_news=False, show_type='Scripted'):
        return {
            'id': title.lower().replace(' ', '-'),
            'title': title,
            'url': 'https://example.com/watch',
            'details_url': '',
            'genre': ', '.join(genres),
            'genres': genres,
            'thumbnail': '',
            'content_type': 'tv',
            'source_type': 'tvmaze',
            'description': '',
            'release_year': 2026,
            'rating': None,
            'external_source': 'tvmaze',
            'external_id': title,
            'is_external': True,
            'is_live_source': True,
            'provider': 'Example Network',
            'network': 'Example Network',
            'access_type': 'other',
            'action_label': 'Watch on Example Network',
            'episode_label': 'S1 E1',
            'airtime': '20:00',
            'runtime': 60,
            'show_type': show_type,
            'is_news': is_news,
        }

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='viewer', password='test-password'
        )
        self.news_user = get_user_model().objects.create_user(
            username='newsviewer', password='test-password'
        )

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule')
    def test_default_experience_does_not_globally_hide_news(self, mock_live, *_mocks):
        mock_live.return_value = [
            self._item('Evening News', ['News'], is_news=True, show_type='News'),
            self._item('Funny Show', ['Comedy']),
        ]
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Evening News')
        self.assertContains(response, 'Funny Show')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule')
    def test_user_can_save_preferences_without_news(self, mock_live, *_mocks):
        mock_live.return_value = [
            self._item('Evening News', ['News'], is_news=True, show_type='News'),
            self._item('Police Drama', ['Crime', 'Drama']),
        ]
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('home'),
            {
                'action': 'save_discovery_preferences',
                'preferred_genres': ['Comedy', 'Crime', 'Drama'],
            },
        )
        self.assertRedirects(response, reverse('home'))

        preference = DiscoveryPreference.objects.get(user=self.user)
        self.assertTrue(preference.customized)
        self.assertEqual(preference.preferred_genres, ['Comedy', 'Crime', 'Drama'])

        response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'Evening News')
        self.assertContains(response, 'Police Drama')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule')
    def test_preferences_are_isolated_per_user(self, mock_live, *_mocks):
        mock_live.return_value = [
            self._item('Evening News', ['News'], is_news=True, show_type='News'),
            self._item('Police Drama', ['Crime', 'Drama']),
        ]
        DiscoveryPreference.objects.create(
            user=self.user,
            preferred_genres=['Crime', 'Drama'],
            customized=True,
        )
        DiscoveryPreference.objects.create(
            user=self.news_user,
            preferred_genres=['News'],
            customized=True,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'Evening News')
        self.assertContains(response, 'Police Drama')

        self.client.force_login(self.news_user)
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Evening News')
        self.assertNotContains(response, 'Police Drama')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule', return_value=[])
    def test_news_is_a_normal_genre_choice_not_a_disable_news_control(self, *_mocks):
        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Tune my discovery')
        self.assertContains(response, 'value="News"', html=False)
        self.assertNotContains(response, 'Include news/current affairs')
        self.assertNotContains(response, 'News is hidden by default')
