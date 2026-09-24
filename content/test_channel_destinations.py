from django.db import IntegrityError, transaction
from django.test import TestCase

from content.models import Channel, ChannelDestination


class ChannelDestinationTests(TestCase):
    def setUp(self):
        self.channel = Channel.objects.create(
            name='Example Network',
            slug='example-network',
            region='US',
            source='fixture',
            external_id='network-1',
        )

    def test_destination_identity_is_unique_per_channel_source_and_url(self):
        values = {
            'channel': self.channel,
            'provider': 'Example',
            'url': 'https://example.com/live',
            'access_type': 'free',
            'destination_type': ChannelDestination.DestinationType.DIRECT,
            'source': 'fixture',
        }
        ChannelDestination.objects.create(**values)

        with self.assertRaises(IntegrityError), transaction.atomic():
            ChannelDestination.objects.create(**values)

    def test_only_direct_and_tuner_destinations_are_playable(self):
        direct = ChannelDestination(
            channel=self.channel,
            provider='Direct Provider',
            url='https://example.com/direct',
            destination_type=ChannelDestination.DestinationType.DIRECT,
            source='fixture',
        )
        tuner = ChannelDestination(
            channel=self.channel,
            provider='Home Tuner',
            url='https://example.com/tuner',
            destination_type=ChannelDestination.DestinationType.TUNER,
            source='fixture',
        )
        provider = ChannelDestination(
            channel=self.channel,
            provider='Provider Listing',
            url='https://example.com/provider',
            destination_type=ChannelDestination.DestinationType.PROVIDER,
            source='fixture',
        )
        details = ChannelDestination(
            channel=self.channel,
            provider='Details',
            url='https://example.com/details',
            destination_type=ChannelDestination.DestinationType.DETAILS,
            source='fixture',
        )

        self.assertTrue(direct.is_playable)
        self.assertTrue(tuner.is_playable)
        self.assertFalse(provider.is_playable)
        self.assertFalse(details.is_playable)

    def test_action_labels_preserve_access_semantics(self):
        destination = ChannelDestination(
            channel=self.channel,
            provider='Cable Network',
            url='https://example.com/live',
            access_type='auth',
            destination_type=ChannelDestination.DestinationType.DIRECT,
            source='fixture',
        )
        tuner = ChannelDestination(
            channel=self.channel,
            provider='Living Room Tuner',
            url='https://example.com/tuner',
            destination_type=ChannelDestination.DestinationType.TUNER,
            source='fixture',
        )

        self.assertEqual(destination.action_label, 'Cable Network · Sign-in required')
        self.assertEqual(tuner.action_label, 'Watch via Living Room Tuner')
