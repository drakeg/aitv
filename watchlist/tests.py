from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from content.models import ContentItem
from .models import Watchlist


class WatchlistFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='viewer', password='test-password')
        self.item = ContentItem.objects.create(
            title='Watch Me',
            url='https://example.com/watch-me',
            genre='Drama',
            content_type=ContentItem.ContentType.TV,
            source_type='web',
        )

    def test_watchlist_page_requires_login(self):
        response = self.client.get(reverse('watchlist:list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_add_and_remove_are_post_only(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('watchlist:add', args=[self.item.id])).status_code, 405)
        self.assertEqual(self.client.get(reverse('watchlist:remove', args=[self.item.id])).status_code, 405)

    def test_user_can_add_view_and_remove_watchlist_item(self):
        self.client.force_login(self.user)

        add_response = self.client.post(reverse('watchlist:add', args=[self.item.id]))
        self.assertEqual(add_response.status_code, 302)
        self.assertTrue(Watchlist.objects.filter(user=self.user, content=self.item).exists())

        page = self.client.get(reverse('watchlist:list'))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Watch Me')

        remove_response = self.client.post(
            reverse('watchlist:remove', args=[self.item.id]),
            {'next': reverse('watchlist:list')},
        )
        self.assertRedirects(remove_response, reverse('watchlist:list'))
        self.assertFalse(Watchlist.objects.filter(user=self.user, content=self.item).exists())

    def test_async_add_and_remove_return_state_without_redirect(self):
        self.client.force_login(self.user)
        headers = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

        add_response = self.client.post(
            reverse('watchlist:add', args=[self.item.id]),
            **headers,
        )
        self.assertEqual(add_response.status_code, 200)
        self.assertJSONEqual(
            add_response.content,
            {
                'saved': True,
                'content_id': self.item.id,
                'label': '✓ Saved to Watchlist',
                'add_url': reverse('watchlist:add', args=[self.item.id]),
                'remove_url': reverse('watchlist:remove', args=[self.item.id]),
            },
        )

        remove_response = self.client.post(
            reverse('watchlist:remove', args=[self.item.id]),
            **headers,
        )
        self.assertEqual(remove_response.status_code, 200)
        self.assertJSONEqual(
            remove_response.content,
            {
                'saved': False,
                'content_id': self.item.id,
                'label': '⭐ Save to Watchlist',
                'add_url': reverse('watchlist:add', args=[self.item.id]),
                'remove_url': reverse('watchlist:remove', args=[self.item.id]),
            },
        )
        self.assertFalse(Watchlist.objects.filter(user=self.user, content=self.item).exists())
