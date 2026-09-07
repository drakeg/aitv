from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from content.models import DiscoveryPreference


@patch('core.views.fetch_free_archive_movies', return_value=[])
@patch('core.views.fetch_trending_movies', return_value=[])
@patch('core.views.fetch_popular_tv', return_value=[])
@patch('core.views.fetch_tv_on_the_air', return_value=[])
@patch('core.views.fetch_trending_tv', return_value=[])
@patch('core.views.fetch_live_tv_schedule', return_value=[])
class PreferenceResetTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='viewer', password='test-password')
        self.client.force_login(self.user)

    def test_empty_category_submission_restores_neutral_discovery(self, *_mocks):
        preference = DiscoveryPreference.objects.create(
            user=self.user,
            preferred_genres=['Crime', 'Drama'],
            customized=True,
            region='US',
            require_region_availability=True,
            content_mix=DiscoveryPreference.ContentMix.TV_FIRST,
        )

        response = self.client.post(reverse('profile'), {
            'action': 'discovery',
            'region': 'US',
            'require_region_availability': '1',
            'content_mix': DiscoveryPreference.ContentMix.TV_FIRST,
        })

        self.assertRedirects(response, reverse('profile'))
        preference.refresh_from_db()
        self.assertFalse(preference.customized)
        self.assertEqual(preference.preferred_genres, [])
        self.assertEqual(preference.region, 'US')
        self.assertTrue(preference.require_region_availability)
        self.assertEqual(preference.content_mix, DiscoveryPreference.ContentMix.TV_FIRST)

    def test_explicit_show_all_categories_reset_preserves_other_settings(self, *_mocks):
        preference = DiscoveryPreference.objects.create(
            user=self.user,
            preferred_genres=['Comedy'],
            customized=True,
            region='CA',
            require_region_availability=True,
            content_mix=DiscoveryPreference.ContentMix.MOVIES_FIRST,
        )

        response = self.client.post(reverse('profile'), {
            'action': 'reset_categories',
            'preferred_genres': ['Comedy'],
            'region': 'CA',
            'require_region_availability': '1',
            'content_mix': DiscoveryPreference.ContentMix.MOVIES_FIRST,
        })

        self.assertRedirects(response, reverse('profile'))
        preference.refresh_from_db()
        self.assertFalse(preference.customized)
        self.assertEqual(preference.preferred_genres, [])
        self.assertEqual(preference.region, 'CA')
        self.assertTrue(preference.require_region_availability)
        self.assertEqual(preference.content_mix, DiscoveryPreference.ContentMix.MOVIES_FIRST)

    def test_profile_explains_show_all_categories_behavior(self, *_mocks):
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'Leaving every category unchecked means show all categories')
        self.assertContains(response, 'Show all categories')
