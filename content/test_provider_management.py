from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from content.models import ContentAvailability, ContentItem


class ProviderManagementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='provider-editor',
            password='test-password',
        )
        self.client.force_login(self.user)
        self.item = ContentItem.objects.create(
            title='Example Show',
            url='https://example.com/show',
            genre='Drama',
            source_type='manual',
            content_type='tv',
        )

    def test_edit_page_renders_provider_management(self):
        response = self.client.get(reverse('content:edit', args=[self.item.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Watch providers')
        self.assertContains(response, 'availability-TOTAL_FORMS')

    def test_user_can_add_multiple_provider_destinations(self):
        response = self.client.post(
            reverse('content:edit', args=[self.item.id]),
            {
                'title': self.item.title,
                'url': self.item.url,
                'genre': self.item.genre,
                'content_type': self.item.content_type,
                'availability-TOTAL_FORMS': '2',
                'availability-INITIAL_FORMS': '0',
                'availability-MIN_NUM_FORMS': '0',
                'availability-MAX_NUM_FORMS': '1000',
                'availability-0-provider': 'PBS',
                'availability-0-url': 'https://www.pbs.org/show/example/',
                'availability-0-access_type': 'free',
                'availability-1-provider': 'Tubi',
                'availability-1-url': 'https://tubitv.com/series/example',
                'availability-1-access_type': 'ads',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.item.availabilities.count(), 2)
        self.assertTrue(self.item.availabilities.filter(provider='PBS').exists())
        self.assertTrue(self.item.availabilities.filter(provider='Tubi').exists())

    def test_user_can_remove_existing_provider_destination(self):
        availability = ContentAvailability.objects.create(
            content=self.item,
            provider='CBS',
            url='https://www.cbs.com/shows/example/',
            access_type='other',
        )

        response = self.client.post(
            reverse('content:edit', args=[self.item.id]),
            {
                'title': self.item.title,
                'url': self.item.url,
                'genre': self.item.genre,
                'content_type': self.item.content_type,
                'availability-TOTAL_FORMS': '1',
                'availability-INITIAL_FORMS': '1',
                'availability-MIN_NUM_FORMS': '0',
                'availability-MAX_NUM_FORMS': '1000',
                'availability-0-id': str(availability.id),
                'availability-0-provider': availability.provider,
                'availability-0-url': availability.url,
                'availability-0-access_type': availability.access_type,
                'availability-0-DELETE': 'on',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(ContentAvailability.objects.filter(id=availability.id).exists())
