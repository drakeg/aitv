import os
from datetime import timedelta
from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from content.models import EpgRefreshState


class HealthEndpointTests(TestCase):
    def test_liveness_reports_database_ok(self):
        response = self.client.get(reverse('health_live'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'database': 'ok'})

    @patch('core.views.connection.cursor', side_effect=DatabaseError('database down'))
    def test_liveness_returns_503_when_database_is_unavailable(self, _cursor):
        response = self.client.get(reverse('health_live'))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unhealthy', 'database': 'unavailable'})

    def test_readiness_is_503_when_expected_epg_state_is_missing(self):
        with patch.dict(os.environ, {'EPG_REGIONS': 'US', 'EPG_STALE_AFTER_SECONDS': '7200'}):
            response = self.client.get(reverse('health_ready'))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['status'], 'degraded')
        self.assertEqual(response.json()['epg'][0]['status'], 'missing')

    def test_readiness_is_200_for_fresh_successful_regions(self):
        now = timezone.now()
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            refreshed_at=now - timedelta(minutes=15),
            attempted_at=now - timedelta(minutes=15),
            airing_count=12,
            status=EpgRefreshState.Status.SUCCESS,
        )
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='CA',
            refreshed_at=now - timedelta(minutes=20),
            attempted_at=now - timedelta(minutes=20),
            airing_count=8,
            status=EpgRefreshState.Status.SUCCESS,
        )

        with patch.dict(os.environ, {'EPG_REGIONS': 'US,CA', 'EPG_STALE_AFTER_SECONDS': '7200'}):
            response = self.client.get(reverse('health_ready'))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['status'], 'ready')
        self.assertEqual([item['region'] for item in body['epg']], ['US', 'CA'])
        self.assertTrue(all(item['status'] == 'ok' for item in body['epg']))

    def test_readiness_is_503_for_stale_or_failed_region_without_error_details(self):
        now = timezone.now()
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            refreshed_at=now - timedelta(hours=3),
            attempted_at=now - timedelta(minutes=1),
            airing_count=9,
            status=EpgRefreshState.Status.FAILURE,
            last_error='ScheduleFetchError: secret detail',
        )

        with patch.dict(os.environ, {'EPG_REGIONS': 'US', 'EPG_STALE_AFTER_SECONDS': '7200'}):
            response = self.client.get(reverse('health_ready'))

        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual(body['epg'][0]['status'], 'failed')
        self.assertNotIn('last_error', body['epg'][0])
        self.assertNotIn('secret detail', response.content.decode())

    def test_readiness_marks_old_success_as_stale(self):
        now = timezone.now()
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            refreshed_at=now - timedelta(hours=3),
            attempted_at=now - timedelta(hours=3),
            airing_count=4,
            status=EpgRefreshState.Status.SUCCESS,
        )

        with patch.dict(os.environ, {'EPG_REGIONS': 'US', 'EPG_STALE_AFTER_SECONDS': '7200'}):
            response = self.client.get(reverse('health_ready'))

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['epg'][0]['status'], 'stale')
