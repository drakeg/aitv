from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from content.models import DiscoveryPreference


class ProviderPreferenceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='viewer', password='test-password')
        self.client.force_login(self.user)

    def test_profile_saves_provider_choices_per_account(self):
        response = self.client.post(reverse('profile'), {
            'action': 'discovery',
            'region': 'US',
            'content_mix': DiscoveryPreference.ContentMix.BALANCED,
            'preferred_genres': ['Comedy'],
            'preferred_providers': ['Hulu', 'Tubi TV', 'Not A Provider'],
            'require_region_availability': '1',
        })
        self.assertEqual(response.status_code, 302)
        preference = DiscoveryPreference.objects.get(user=self.user)
        self.assertEqual(preference.preferred_providers, ['Hulu', 'Tubi TV'])

    def test_home_exposes_only_signed_in_viewers_provider_preferences(self):
        preference = DiscoveryPreference.objects.create(user=self.user, preferred_providers=['Hulu', 'Tubi TV'])
        with self.settings(TMDB_API_KEY='', TMDB_READ_ACCESS_TOKEN=''):
            response = self.client.get(reverse('home'))
        self.assertEqual(response.context['preferred_providers'], preference.preferred_providers)
        self.client.logout()
        with self.settings(TMDB_API_KEY='', TMDB_READ_ACCESS_TOKEN=''):
            anonymous = self.client.get(reverse('home'))
        self.assertEqual(anonymous.context['preferred_providers'], [])

    def test_client_prioritizes_selected_providers_stably(self):
        script = Path(settings.BASE_DIR, 'static', 'js', 'tmdb-context.js').read_text()
        self.assertIn('preferredProviderOrder', script)
        self.assertIn('if (!preferredProviderOrder.size) return rows || []', script)
        self.assertIn('if (leftPreferred !== rightPreferred) return leftPreferred ? -1 : 1', script)
        self.assertIn('return left.index - right.index', script)
        self.assertIn('const allRows = providerRows(data)', script)
