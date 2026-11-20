from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from content.admin import ChannelDestinationAdminForm, EpgRefreshStateAdmin, _age_label
from content.models import Airing, AiringDestination, Channel, ChannelDestination, ChannelFavorite, EpgRefreshState, Program


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
        for model in (Channel, ChannelDestination, Program, Airing, AiringDestination, EpgRefreshState, ChannelFavorite):
            self.assertIn(model, admin.site._registry)

    def test_normalized_source_models_cannot_be_added_or_deleted_in_admin(self):
        for model in (Channel, Program, Airing, AiringDestination, EpgRefreshState, ChannelFavorite):
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


    def test_refresh_state_admin_uses_shared_health_policy_without_queries(self):
        now = timezone.now()
        state = EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            status=EpgRefreshState.Status.SUCCESS,
            attempted_at=now - timezone.timedelta(minutes=5),
            refreshed_at=now - timezone.timedelta(minutes=10),
            airing_count=42,
        )
        model_admin = EpgRefreshStateAdmin(EpgRefreshState, admin.site)

        with patch('content.admin.timezone.now', return_value=now):
            with self.assertNumQueries(0):
                self.assertEqual(model_admin.health_status(state), 'OK')
                self.assertEqual(model_admin.attempt_age(state), '5 min ago')
                self.assertEqual(model_admin.success_age(state), '10 min ago')

    def test_refresh_state_admin_surfaces_stale_and_failed_health(self):
        now = timezone.now()
        stale = EpgRefreshState(
            source='tvmaze',
            region='US',
            status=EpgRefreshState.Status.SUCCESS,
            attempted_at=now - timezone.timedelta(hours=3),
            refreshed_at=now - timezone.timedelta(hours=3),
            airing_count=10,
        )
        failed = EpgRefreshState(
            source='tvmaze',
            region='CA',
            status=EpgRefreshState.Status.FAILURE,
            attempted_at=now - timezone.timedelta(minutes=2),
            refreshed_at=now - timezone.timedelta(minutes=30),
            airing_count=7,
            last_error='operator-only upstream detail',
        )
        model_admin = EpgRefreshStateAdmin(EpgRefreshState, admin.site)

        with patch('content.admin.timezone.now', return_value=now):
            self.assertEqual(model_admin.health_status(stale), 'STALE')
            self.assertEqual(model_admin.health_status(failed), 'FAILED')

    @patch.dict('os.environ', {'EPG_REGIONS': 'US,CA', 'EPG_STALE_AFTER_SECONDS': '7200'})
    def test_refresh_state_changelist_warns_about_degraded_configured_regions_without_error_detail(self):
        now = timezone.now()
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            status=EpgRefreshState.Status.FAILURE,
            attempted_at=now,
            refreshed_at=now - timezone.timedelta(minutes=20),
            airing_count=5,
            last_error='secret upstream exception detail',
        )

        response = self.client.get(reverse('admin:content_epgrefreshstate_changelist'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EPG diagnostics: US failed, CA missing.')
        self.assertContains(response, 'Health')
        self.assertContains(response, 'Attempt age')
        self.assertContains(response, 'Success age')
        self.assertNotContains(response, 'secret upstream exception detail')

    def test_refresh_state_change_page_keeps_raw_failure_detail_operator_only(self):
        state = EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            status=EpgRefreshState.Status.FAILURE,
            attempted_at=timezone.now(),
            last_error='operator-only failure summary',
        )

        response = self.client.get(
            reverse('admin:content_epgrefreshstate_change', args=[state.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Operator-only failure detail')
        self.assertContains(response, 'operator-only failure summary')


class EpgAdminAgeLabelTests(TestCase):
    def test_age_label_uses_compact_operator_friendly_units(self):
        now = timezone.now()

        self.assertEqual(_age_label(None, now=now), 'Never')
        self.assertEqual(
            _age_label(now - timezone.timedelta(seconds=20), now=now),
            '<1 min ago',
        )
        self.assertEqual(
            _age_label(now - timezone.timedelta(minutes=12), now=now),
            '12 min ago',
        )
        self.assertEqual(
            _age_label(now - timezone.timedelta(hours=3), now=now),
            '3 hr ago',
        )
        self.assertEqual(
            _age_label(now - timezone.timedelta(days=3), now=now),
            '3 days ago',
        )
