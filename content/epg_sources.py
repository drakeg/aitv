from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, Protocol

from django.utils import timezone


class ScheduleSourceAdapter(Protocol):
    """Contract for a trusted schedule source normalized before persistence."""

    source: str

    def fetch_airings(self, *, region: str, limit: int = 1000) -> list[dict]:
        """Return normalized airing rows for one region."""


@dataclass(frozen=True)
class TvmazeScheduleAdapter:
    """Normalize TVmaze discovery rows into the shared EPG source contract."""

    fetch_schedule: Callable
    source: str = 'tvmaze'

    def fetch_airings(self, *, region: str, limit: int = 1000) -> list[dict]:
        items = self.fetch_schedule(limit=limit, country=region)
        now = timezone.now()
        rows = []

        for item in items:
            if not isinstance(item, dict):
                continue

            airtime = str(item.get('airtime') or '').strip()
            try:
                hour, minute = [int(part) for part in airtime.split(':', 1)]
                starts_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            except (TypeError, ValueError):
                continue

            runtime = item.get('runtime')
            try:
                runtime_minutes = int(runtime)
            except (TypeError, ValueError):
                runtime_minutes = 30
            if runtime_minutes <= 0:
                runtime_minutes = 30

            rows.append({
                'airing_external_id': str(item.get('schedule_external_id') or ''),
                'channel_external_id': str(item.get('channel_external_id') or ''),
                'program_external_id': str(item.get('external_id') or ''),
                'channel_name': item.get('network') or 'TV',
                'channel_categories': item.get('genres') or [],
                'program_title': item.get('title') or 'Untitled',
                'program_description': item.get('description') or '',
                'program_type': item.get('show_type') or '',
                'starts_at': starts_at,
                'ends_at': starts_at + timedelta(minutes=runtime_minutes),
                'destination_url': item.get('watch_url') or '',
                'destination_provider': item.get('provider') or '',
                'destination_access_type': item.get('access_type') or '',
                'destination_scope': item.get('watch_scope') or '',
            })

        return rows
