from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Protocol


class ScheduleNormalizationError(RuntimeError):
    """A non-empty source snapshot could not produce any valid normalized airings."""


class ScheduleSourceAdapter(Protocol):
    """Contract for a trusted schedule source normalized before persistence."""

    source: str
    complete_snapshot: bool

    def fetch_airings(self, *, region: str, limit: int | None = 1000) -> list[dict]:
        """Return normalized airing rows for one region."""


@dataclass(frozen=True)
class TvmazeScheduleAdapter:
    """Normalize TVmaze discovery rows into the shared EPG source contract."""

    fetch_schedule: Callable
    source: str = 'tvmaze'
    complete_snapshot: bool = True

    def fetch_airings(self, *, region: str, limit: int | None = 1000) -> list[dict]:
        items = self.fetch_schedule(limit=limit, country=region)
        rows = []
        rejected_rows = 0
        seen_airings = {}

        for item in items:
            if not isinstance(item, dict):
                rejected_rows += 1
                continue

            # TVmaze's airstamp includes the actual calendar date and UTC offset.
            # A bare airtime cannot represent midnight or a different network timezone.
            airstamp = item.get('airstamp')
            if not isinstance(airstamp, str) or not airstamp.strip():
                rejected_rows += 1
                continue
            try:
                starts_at = datetime.fromisoformat(airstamp.strip())
            except ValueError:
                rejected_rows += 1
                continue
            if starts_at.tzinfo is None or starts_at.utcoffset() is None:
                rejected_rows += 1
                continue

            airing_external_id = str(item.get('schedule_external_id') or '').strip()
            channel_external_id = str(item.get('channel_external_id') or '').strip()
            program_external_id = str(item.get('external_id') or '').strip()
            if not airing_external_id or not channel_external_id or not program_external_id:
                rejected_rows += 1
                continue

            runtime = item.get('runtime')
            try:
                runtime_minutes = int(runtime)
            except (TypeError, ValueError):
                runtime_minutes = 30
            if runtime_minutes <= 0:
                runtime_minutes = 30

            identity = (channel_external_id, program_external_id, starts_at, starts_at + timedelta(minutes=runtime_minutes))
            previous_identity = seen_airings.get(airing_external_id)
            if previous_identity is not None:
                if previous_identity != identity:
                    rejected_rows += 1
                continue
            seen_airings[airing_external_id] = identity

            rows.append({
                'airing_external_id': airing_external_id,
                'channel_external_id': channel_external_id,
                'program_external_id': program_external_id,
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

        if rejected_rows:
            raise ScheduleNormalizationError(
                'TVmaze returned schedule rows that could not all be normalized'
            )

        return rows
