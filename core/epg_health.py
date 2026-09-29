import os

from django.utils import timezone

from content.models import EpgRefreshState


DEFAULT_EPG_REGION = 'US'
DEFAULT_EPG_STALE_AFTER_SECONDS = 7200


def configured_epg_regions():
    raw = os.getenv('EPG_REGIONS', DEFAULT_EPG_REGION)
    regions = []
    for value in str(raw).split(','):
        region = value.strip().upper()
        if len(region) == 2 and region.isalpha() and region not in regions:
            regions.append(region)
    return regions or [DEFAULT_EPG_REGION]


def epg_stale_after_seconds():
    try:
        value = int(os.getenv('EPG_STALE_AFTER_SECONDS', str(DEFAULT_EPG_STALE_AFTER_SECONDS)))
    except ValueError:
        return DEFAULT_EPG_STALE_AFTER_SECONDS
    return max(1, value)


def evaluate_epg_state(state, *, now=None, stale_after_seconds=None):
    now = now or timezone.now()
    stale_after_seconds = stale_after_seconds or epg_stale_after_seconds()

    if state is None:
        return 'missing'
    if state.status == EpgRefreshState.Status.FAILURE:
        return 'failed'
    if state.refreshed_at is None:
        return 'stale'
    if state.refreshed_at < now - timezone.timedelta(seconds=stale_after_seconds):
        return 'stale'
    return 'ok'


def epg_region_health(region, *, now=None, stale_after_seconds=None):
    state = EpgRefreshState.objects.filter(source='tvmaze', region=region).first()
    return state, evaluate_epg_state(
        state,
        now=now,
        stale_after_seconds=stale_after_seconds,
    )


def configured_epg_health(*, now=None, stale_after_seconds=None):
    now = now or timezone.now()
    stale_after_seconds = stale_after_seconds or epg_stale_after_seconds()
    regions = configured_epg_regions()
    states = {
        state.region: state
        for state in EpgRefreshState.objects.filter(
            source='tvmaze',
            region__in=regions,
        )
    }

    results = []
    for region in regions:
        state = states.get(region)
        results.append((
            region,
            state,
            evaluate_epg_state(
                state,
                now=now,
                stale_after_seconds=stale_after_seconds,
            ),
        ))
    return results
