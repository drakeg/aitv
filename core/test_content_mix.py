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
class ContentMixPreferenceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='viewer', password='test-password')
        self.client.force_login(self.user)

    def test_profile_exposes_neutral_tv_first_and_movies_first_choices(self, *_mocks):
        response = self.client.get(reverse('profile'))

        self.assertContains(response, 'What I watch')
        self.assertContains(response, 'value="balanced"', html=False)
        self.assertContains(response, 'value="tv_first"', html=False)
        self.assertContains(response, 'value="movies_first"', html=False)

    def test_tv_first_preference_is_saved(self, *_mocks):
        response = self.client.post(reverse('profile'), {
            'action': 'discovery',
            'preferred_genres': ['Comedy', 'Crime', 'Drama'],
            'region': 'US',
            'require_region_availability': '1',
            'content_mix': 'tv_first',
        })

        self.assertRedirects(response, reverse('profile'))
        preference = DiscoveryPreference.objects.get(user=self.user)
        self.assertEqual(preference.content_mix, DiscoveryPreference.ContentMix.TV_FIRST)

    def test_invalid_content_mix_falls_back_to_balanced(self, *_mocks):
        self.client.post(reverse('profile'), {
            'action': 'discovery',
            'preferred_genres': ['Drama'],
            'region': 'US',
            'content_mix': 'invalid-value',
        })

        preference = DiscoveryPreference.objects.get(user=self.user)
        self.assertEqual(preference.content_mix, DiscoveryPreference.ContentMix.BALANCED)

    def test_section_order_changes_per_account(self, *_mocks):
        preference = DiscoveryPreference.objects.create(
            user=self.user,
            content_mix=DiscoveryPreference.ContentMix.MOVIES_FIRST,
        )

        response = self.client.get(reverse('home'))
        content = response.content.decode()
        self.assertLess(content.index('Watch Free Now'), content.index('On TV Today'))

        preference.content_mix = DiscoveryPreference.ContentMix.TV_FIRST
        preference.save(update_fields=['content_mix'])
        response = self.client.get(reverse('home'))
        content = response.content.decode()
        self.assertLess(content.index('Popular TV'), content.index('Watch Free Now'))

    def test_balanced_default_interleaves_movie_rows_before_later_tv_rows(self, *_mocks):
        response = self.client.get(reverse('home'))
        content = response.content.decode()

        self.assertLess(content.index('Trending TV Today'), content.index('Watch Free Now'))
        self.assertLess(content.index('Trending Movies'), content.index('TV On the Air'))
