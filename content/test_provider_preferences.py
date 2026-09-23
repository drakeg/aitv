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
        self.assertIn('const hasPreferredProvider = (data)', script)
        self.assertIn("card.dataset.preferredProviderMatch = matchedProviders.length ? '1' : '0'", script)
        self.assertIn("badge.textContent = matchedProviders.length ? `On ${matchedProviders[0]}` : ''", script)
        self.assertIn("badge.classList.toggle('d-none', !matchedProviders.length)", script)
        self.assertIn("if (!card || !preferredProviderOrder.size) return", script)
        self.assertIn("[data-favorite-form][data-favorite-state=\"1\"]", script)
        self.assertIn("row.insertBefore(card, anchor)", script)
        self.assertIn("const bestProvider = providerRows(data)[0]", script)
        self.assertIn("preferredProviderOrder.has(providerName.toLocaleLowerCase())", script)
        self.assertIn("return `See ${providerName} subscription options`", script)

    def test_cards_expose_neutral_provider_match_state(self):
        template = Path(settings.BASE_DIR, 'templates', 'partials', 'card.html').read_text()
        self.assertIn('data-preferred-provider-match="0"', template)
        self.assertIn('data-preferred-provider-badge', template)


    def test_provider_personalization_documentation_tracks_current_behavior(self):
        readme = Path(settings.BASE_DIR, 'README.md').read_text()
        product_doc = Path(settings.BASE_DIR, 'docs', 'product-preferences.md').read_text()
        refresh_doc = Path(settings.BASE_DIR, 'docs', 'content-refresh.md').read_text()
        for document in (readme, product_doc, refresh_doc):
            self.assertIn('On <provider>', document)
        self.assertIn('Definition of done', readme)
        self.assertIn('implementation, tests, and documentation synchronized', readme)
