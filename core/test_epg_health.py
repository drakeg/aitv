import os
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from content.models import EpgRefreshState
from core.epg_health import (
    configured_epg_health,
    configured_epg_regions,
    epg_region_health,
    epg_stale_after_seconds,
)


class EpgHealthPolicyTests(TestCase):
    def test_configured_regions_are_normalized_and_deduplicated(self):
        with patch.dict(os.environ, {'EPG_REGIONS': 'us, CA,US,bad'}, clear=False):
            self.assertEqual(configured_epg_regions(), ['US', 'CA'])

    def test_invalid_stale_threshold_falls_back_and_zero_clamps(self):
        with patch.dict(os.environ, {'EPG_STALE_AFTER_SECONDS': 'invalid'}, clear=False):
            self.assertEqual(epg_stale_after_seconds(), 7200)
        with patch.dict(os.environ, {'EPG_STALE_AFTER_SECONDS': '0'}, clear=False):
            self.assertEqual(epg_stale_after_seconds(), 1)

    def test_region_health_distinguishes_missing_failed_stale_and_ok(self):
        now = timezone.now()

        state, health = epg_region_health('US', now=now, stale_after_seconds=7200)
        self.assertIsNone(state)
        self.assertEqual(health, 'missing')

        state = EpgRefreshState.objects.create(
            source='tvmaze', region='US',
            refreshed_at=now - timedelta(minutes=10),
            attempted_at=now - timedelta(minutes=1),
            airing_count=10,
            status=EpgRefreshState.Status.FAILURE,
        )
        _, health = epg_region_health('US', now=now, stale_after_seconds=7200)
        self.assertEqual(health, 'failed')

        state.status = EpgRefreshState.Status.SUCCESS
        state.refreshed_at = now - timedelta(hours=3)
        state.save(update_fields=['status', 'refreshed_at'])
        _, health = epg_region_health('US', now=now, stale_after_seconds=7200)
        self.assertEqual(health, 'stale')

        state.refreshed_at = now - timedelta(minutes=30)
        state.save(update_fields=['refreshed_at'])
        _, health = epg_region_health('US', now=now, stale_after_seconds=7200)
        self.assertEqual(health, 'ok')

    def test_configured_health_preserves_configured_region_order(self):
        now = timezone.now()
        for region in ('US', 'CA'):
            EpgRefreshState.objects.create(
                source='tvmaze', region=region,
                refreshed_at=now - timedelta(minutes=5),
                attempted_at=now - timedelta(minutes=5),
                airing_count=1,
                status=EpgRefreshState.Status.SUCCESS,
            )

        with patch.dict(os.environ, {'EPG_REGIONS': 'CA,US'}, clear=False):
            result = configured_epg_health(now=now, stale_after_seconds=7200)

        self.assertEqual([(region, health) for region, _state, health in result], [('CA', 'ok'), ('US', 'ok')])
