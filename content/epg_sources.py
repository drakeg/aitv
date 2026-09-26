from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Protocol



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
        rows = []

        for item in items:
            if not isinstance(item, dict):
                continue

            # TVmaze's airstamp includes the actual calendar date and UTC offset.
            # A bare airtime cannot represent midnight or a different network timezone.
            airstamp = item.get('airstamp')
            if not isinstance(airstamp, str) or not airstamp.strip():
                continue
            try:
                starts_at = datetime.fromisoformat(airstamp.strip())
            except ValueError:
                continue
            if starts_at.tzinfo is None or starts_at.utcoffset() is None:
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
