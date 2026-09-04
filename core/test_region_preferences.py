from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from content.models import DiscoveryPreference


@patch('core.views.fetch_popular_tv', return_value=[])
@patch('core.views.fetch_tv_on_the_air', return_value=[])
@patch('core.views.fetch_free_archive_movies', return_value=[])
@patch('core.views.fetch_trending_movies', return_value=[])
@patch('core.views.fetch_trending_tv', return_value=[])
@patch('core.views.fetch_live_tv_schedule', return_value=[])
class RegionPreferenceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='viewer', password='test-password')
        self.client.force_login(self.user)

    def test_profile_defaults_to_us_and_requires_local_availability(self, *_mocks):
        response = self.client.get(reverse('profile'))
        preference = DiscoveryPreference.objects.get(user=self.user)

        self.assertEqual(preference.region, 'US')
        self.assertTrue(preference.require_region_availability)
        self.assertContains(response, 'Only show titles with providers in my region')
        self.assertContains(response, '<option value="US" selected>', html=False)

    def test_user_can_change_region_and_availability_filter(self, *_mocks):
        response = self.client.post(reverse('profile'), {
            'preferred_genres': ['Comedy', 'Drama'],
            'region': 'CA',
        })
        self.assertRedirects(response, reverse('profile'))

        preference = DiscoveryPreference.objects.get(user=self.user)
        self.assertEqual(preference.region, 'CA')
        self.assertFalse(preference.require_region_availability)

    def test_region_is_passed_to_live_schedule(self, mock_live, *_mocks):
        DiscoveryPreference.objects.create(
            user=self.user,
            region='CA',
            require_region_availability=True,
        )

        self.client.get(reverse('home'))

        mock_live.assert_called_once_with(limit=100, country='CA')
