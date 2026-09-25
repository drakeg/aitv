from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from content.admin import ChannelDestinationAdminForm
from content.models import Airing, Channel, ChannelDestination, ChannelFavorite, Program


class EpgAdminTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password',
        )
        self.client.force_login(self.user)
        self.request = RequestFactory().get('/admin/')
        self.request.user = self.user
        self.channel = Channel.objects.create(
            name='Example Network',
            slug='example-network',
            region='US',
            source='tvmaze',
            external_id='network-1',
        )

    def test_epg_models_are_registered(self):
        for model in (Channel, ChannelDestination, Program, Airing, ChannelFavorite):
            self.assertIn(model, admin.site._registry)

    def test_normalized_source_models_cannot_be_added_or_deleted_in_admin(self):
        for model in (Channel, Program, Airing, ChannelFavorite):
            model_admin = admin.site._registry[model]
            self.assertFalse(model_admin.has_add_permission(self.request))
            self.assertFalse(model_admin.has_delete_permission(self.request))

    def test_channel_admin_is_accessible_for_destination_management(self):
        response = self.client.get(reverse('admin:content_channel_change', args=[self.channel.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Channel destinations')
        self.assertContains(response, 'provider')
        self.assertContains(response, 'Destination type')

    def test_destination_admin_accepts_explicit_http_playback_destination(self):
        form = ChannelDestinationAdminForm(data={
            'channel': self.channel.pk,
            'provider': 'Example Stream',
            'url': 'https://example.com/live',
            'access_type': 'free',
            'destination_type': ChannelDestination.DestinationType.DIRECT,
            'source': 'operator',
        })

        self.assertTrue(form.is_valid(), form.errors)

    def test_destination_admin_rejects_non_http_playback_destination(self):
        form = ChannelDestinationAdminForm(data={
            'channel': self.channel.pk,
            'provider': 'Example Stream',
            'url': 'ftp://example.com/live',
            'access_type': 'free',
            'destination_type': ChannelDestination.DestinationType.DIRECT,
            'source': 'operator',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('url', form.errors)
