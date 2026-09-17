import os
from pathlib import Path
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from content.services import fetch_tmdb_watch_context


class ProviderExpansionTests(SimpleTestCase):
    @patch.dict(os.environ, {'TMDB_API_KEY': 'test-key'}, clear=True)
    @patch('content.services.requests.get')
    def test_watch_context_keeps_compact_and_complete_provider_lists(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            'watch/providers': {'results': {'US': {
                'link': 'https://www.themoviedb.org/tv/42/watch',
                'free': [{'provider_name': 'Plex'}],
                'ads': [{'provider_name': 'Tubi'}],
                'flatrate': [{'provider_name': 'Hulu'}, {'provider_name': 'Netflix'}],
            }}},
        }
        mock_get.return_value = response

        context = fetch_tmdb_watch_context('tv', '42', region='US')

        self.assertEqual([row['name'] for row in context['providers']], ['Plex', 'Tubi'])
        self.assertEqual(
            [row['name'] for row in context['all_providers']],
            ['Plex', 'Tubi', 'Hulu', 'Netflix'],
        )
        self.assertEqual(context['additional_provider_count'], 2)

    def test_client_expands_additional_provider_names_in_place(self):
        script = Path('static/js/tmdb-context.js').read_text()

        self.assertIn('data.all_providers || rows', script)
        self.assertIn("more.setAttribute('aria-expanded'", script)
        self.assertIn("container.querySelectorAll('[data-additional-provider]')", script)
        self.assertIn("more.textContent = expanded ? `+${additionalRows.length} more` : 'Show fewer'", script)
