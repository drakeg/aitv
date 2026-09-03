from django.template.loader import render_to_string
from django.test import TestCase

from content.models import ContentAvailability, ContentItem


class ContentCardTemplateTests(TestCase):
    def test_local_content_item_with_title_renders_without_name_attribute(self):
        item = ContentItem.objects.create(
            title='Big Buck Bunny',
            url='https://www.youtube.com/watch?v=aqz-KE-bpKQ',
            genre='Animation',
            thumbnail='https://img.youtube.com/vi/aqz-KE-bpKQ/hqdefault.jpg',
            source_type='youtube',
        )

        rendered = render_to_string(
            'partials/card.html',
            {'item': item, 'watchlist_ids': []},
        )

        self.assertIn('Big Buck Bunny', rendered)

    def test_direct_availability_is_primary_watch_action(self):
        item = ContentItem.objects.create(
            title='FRONTLINE',
            url='https://www.pbs.org/show/frontline/',
            genre='Documentary',
            source_type='network',
            content_type='tv',
        )
        ContentAvailability.objects.create(
            content=item,
            provider='PBS',
            url=item.url,
            access_type='free',
        )

        rendered = render_to_string(
            'partials/card.html',
            {'item': item, 'watchlist_ids': []},
        )

        self.assertIn('Watch on PBS', rendered)
        self.assertNotIn('Open source', rendered)

    def test_tmdb_discovery_loads_compact_watch_context_and_keeps_details_secondary(self):
        rendered = render_to_string(
            'partials/card.html',
            {
                'item': {
                    'id': 'tmdb_tv_7',
                    'title': 'Example Series',
                    'url': 'https://www.themoviedb.org/tv/7',
                    'genre': 'Crime, Drama',
                    'content_type': 'tv',
                    'source_type': 'tmdb',
                    'external_source': 'tmdb',
                    'external_id': '7',
                    'is_external': True,
                },
                'watchlist_ids': [],
            },
        )

        self.assertIn('Crime, Drama', rendered)
        self.assertIn('data-tmdb-context', rendered)
        self.assertIn('data-content-type="tv"', rendered)
        self.assertIn('Loading network, episode, runtime', rendered)
        self.assertIn('Loading watch sources', rendered)
        self.assertIn('See watch options', rendered)
        self.assertIn('TMDB details', rendered)
        self.assertNotIn('Open source', rendered)
