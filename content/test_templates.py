from django.template.loader import render_to_string
from django.test import TestCase

from content.models import ContentItem


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
            {
                'item': item,
                'watchlist_ids': [],
            },
        )

        self.assertIn('Big Buck Bunny', rendered)
