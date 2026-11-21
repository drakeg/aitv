from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from core.models import SystemSettings


@patch('core.views.fetch_free_archive_movies', return_value=[])
@patch('core.views.fetch_live_tv_schedule', return_value=[])
@patch('core.views.fetch_trending_tv', return_value=[])
@patch('core.views.fetch_trending_movies', return_value=[])
class OperatorBrandingTests(TestCase):
    def test_default_brand_remains_aitv_without_operator_settings(self, *_mocks):
        response = self.client.get(reverse('home'))

        self.assertContains(response, '<title>aitv</title>', html=True)
        self.assertContains(response, '🎬 aitv')
        self.assertNotContains(response, 'Welcome to')

    def test_operator_brand_and_welcome_message_are_guest_facing(self, *_mocks):
        settings = SystemSettings.load()
        settings.site_name = 'Pine Ridge Guest TV'
        settings.welcome_message = 'Welcome to Pine Ridge — find what is on and where to watch.'
        settings.save()

        response = self.client.get(reverse('home'))

        self.assertContains(response, '<title>Pine Ridge Guest TV</title>', html=True)
        self.assertContains(response, '🎬 Pine Ridge Guest TV')
        self.assertContains(
            response,
            'Welcome to Pine Ridge — find what is on and where to watch.',
        )

    def test_welcome_message_is_html_escaped(self, *_mocks):
        settings = SystemSettings.load()
        settings.welcome_message = '<script>alert("guest")</script>'
        settings.save()

        response = self.client.get(reverse('home'))

        self.assertNotContains(response, '<script>alert("guest")</script>', html=False)
        self.assertContains(
            response,
            '&lt;script&gt;alert(&quot;guest&quot;)&lt;/script&gt;',
            html=False,
        )

    def test_guest_account_links_remain_visible_by_default(self, *_mocks):
        response = self.client.get(reverse('home'))

        self.assertContains(response, '>Login<', html=False)
        self.assertContains(response, '>Register<', html=False)

    def test_operator_can_hide_guest_account_links(self, *_mocks):
        settings = SystemSettings.load()
        settings.show_guest_account_links = False
        settings.save()

        response = self.client.get(reverse('home'))

        self.assertNotContains(response, '>Login<', html=False)
        self.assertNotContains(response, '>Register<', html=False)
        self.assertContains(response, '>Live TV<', html=False)
