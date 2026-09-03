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
        self.user = get_user_model().objects.create_user(username='viewer', password='test-password')
        self.news_user = get_user_model().objects.create_user(username='newsviewer', password='test-password')

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

    def test_profile_requires_login_and_exposes_all_categories(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)

        self.client.force_login(self.user)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Discovery preferences')
        self.assertContains(response, 'value="News"', html=False)
        self.assertContains(response, 'value="Crime"', html=False)
        self.assertContains(response, 'value="Soap"', html=False)
        self.assertContains(response, 'Soap / Soap Opera')

    def test_profile_saves_name_and_email(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'action': 'account',
            'first_name': 'Viewer',
            'last_name': 'Example',
            'email': 'viewer@example.com',
        })
        self.assertRedirects(response, reverse('profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Viewer')
        self.assertEqual(self.user.last_name, 'Example')
        self.assertEqual(self.user.email, 'viewer@example.com')

    def test_invalid_email_is_rejected(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'action': 'account',
            'email': 'not-an-email',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a valid email address')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, '')

    def test_release_notifications_require_saved_email(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('profile'), {
            'action': 'discovery',
            'preferred_genres': ['Comedy'],
            'region': 'US',
            'require_region_availability': '1',
            'notify_new_releases': '1',
        })
        self.assertRedirects(response, reverse('profile'))
        preference = DiscoveryPreference.objects.get(user=self.user)
        self.assertFalse(preference.notify_new_releases)

        self.user.email = 'viewer@example.com'
        self.user.save(update_fields=['email'])
        self.client.post(reverse('profile'), {
            'action': 'discovery',
            'preferred_genres': ['Comedy'],
            'region': 'US',
            'require_region_availability': '1',
            'notify_new_releases': '1',
        })
        preference.refresh_from_db()
        self.assertTrue(preference.notify_new_releases)

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule')
    def test_user_can_exclude_soap_opera_alias(self, mock_live, *_mocks):
        mock_live.return_value = [
            self._item('Daytime Story', ['Soap Opera'], show_type='Soap Opera'),
            self._item('Police Drama', ['Crime', 'Drama']),
        ]
        DiscoveryPreference.objects.create(
            user=self.user,
            preferred_genres=['Crime', 'Drama'],
            customized=True,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'Daytime Story')
        self.assertContains(response, 'Police Drama')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule')
    def test_user_can_save_preferences_from_profile_without_news(self, mock_live, *_mocks):
        mock_live.return_value = [
            self._item('Evening News', ['News'], is_news=True, show_type='News'),
            self._item('Police Drama', ['Crime', 'Drama']),
        ]
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('profile'),
            {'preferred_genres': ['Comedy', 'Crime', 'Drama']},
        )
        self.assertRedirects(response, reverse('profile'))

        preference = DiscoveryPreference.objects.get(user=self.user)
        self.assertTrue(preference.customized)
        self.assertEqual(preference.preferred_genres, ['Comedy', 'Crime', 'Drama'])

        response = self.client.get(reverse('home'))
        self.assertNotContains(response, 'Evening News')
        self.assertContains(response, 'Police Drama')
        self.assertContains(response, 'Edit preferences')
        self.assertNotContains(response, 'Tune my discovery')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule')
    def test_preferences_are_isolated_per_user(self, mock_live, *_mocks):
        mock_live.return_value = [
            self._item('Evening News', ['News'], is_news=True, show_type='News'),
            self._item('Police Drama', ['Crime', 'Drama']),
        ]
        DiscoveryPreference.objects.create(user=self.user, preferred_genres=['Crime', 'Drama'], customized=True)
        DiscoveryPreference.objects.create(user=self.news_user, preferred_genres=['News'], customized=True)

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
    def test_authenticated_navigation_includes_profile(self, *_mocks):
        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Profile')
        self.assertContains(response, reverse('profile'))
