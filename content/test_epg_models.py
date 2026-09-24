from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from content.models import Airing, Channel, Program


class EpgDomainModelTests(TestCase):
    def setUp(self):
        self.channel = Channel.objects.create(
            name='Example Network',
            slug='example-network',
            region='US',
            source='test-source',
            external_id='channel-1',
            categories=['Entertainment'],
        )
        self.program = Program.objects.create(
            title='Example Show',
            source='test-source',
            external_id='program-1',
            program_type='Scripted',
        )

    def test_channel_identity_is_scoped_by_source_external_id_and_region(self):
        Channel.objects.create(
            name='Canadian Example Network',
            slug='example-network-ca',
            region='CA',
            source='test-source',
            external_id='channel-1',
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Channel.objects.create(
                name='Duplicate',
                slug='duplicate',
                region='US',
                source='test-source',
                external_id='channel-1',
            )

    def test_program_identity_is_scoped_by_source_and_external_id(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Program.objects.create(
                title='Duplicate Show',
                source='test-source',
                external_id='program-1',
            )

    def test_airing_requires_end_after_start(self):
        start = timezone.now()
        Airing.objects.create(
            channel=self.channel,
            program=self.program,
            starts_at=start,
            ends_at=start + timedelta(hours=1),
            source='test-source',
            external_id='airing-1',
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Airing.objects.create(
                channel=self.channel,
                program=self.program,
                starts_at=start,
                ends_at=start,
                source='test-source',
                external_id='airing-invalid',
            )

    def test_schedule_models_do_not_contain_playback_urls(self):
        self.assertNotIn('url', {field.name for field in Channel._meta.fields})
        self.assertNotIn('url', {field.name for field in Program._meta.fields})
        self.assertNotIn('url', {field.name for field in Airing._meta.fields})
