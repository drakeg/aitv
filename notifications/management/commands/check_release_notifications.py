from django.core.management.base import BaseCommand
from django.utils import timezone

from content.models import DiscoveryPreference
from notifications.models import ReleaseNotification, ReleaseWatchState
from notifications.services import fetch_latest_release, send_release_email
from watchlist.models import Watchlist


def _try_release_email(user, notification):
    """Attempt one pending delivery without letting SMTP failures abort the scan."""
    if notification.email_sent_at:
        return False
    try:
        sent = send_release_email(user, notification)
    except Exception:
        return False
    if not sent:
        return False
    notification.email_sent_at = timezone.now()
    notification.save(update_fields=['email_sent_at'])
    return True


class Command(BaseCommand):
    help = 'Check opted-in favorite watchlist titles for newly released episodes.'

    def handle(self, *args, **options):
        created_count = 0
        checked_count = 0
        entries = (
            Watchlist.objects.select_related('user', 'content')
            .filter(
                is_favorite=True,
                user__discovery_preference__notify_new_releases=True,
            )
            .order_by('user_id', 'content_id')
        )

        for entry in entries:
            preference = DiscoveryPreference.objects.filter(user=entry.user).first()
            if not preference or not preference.notify_new_releases or not entry.user.email:
                continue

            release = fetch_latest_release(entry.content)
            if not release:
                continue
            checked_count += 1

            state, created = ReleaseWatchState.objects.get_or_create(
                user=entry.user,
                content=entry.content,
                defaults={'last_event_key': release['event_key']},
            )
            if created:
                continue

            if state.last_event_key == release['event_key']:
                existing = ReleaseNotification.objects.filter(
                    user=entry.user,
                    content=entry.content,
                    event_key=release['event_key'],
                    email_sent_at__isnull=True,
                ).first()
                if existing:
                    _try_release_email(entry.user, existing)
                continue

            notification, notification_created = ReleaseNotification.objects.get_or_create(
                user=entry.user,
                content=entry.content,
                event_key=release['event_key'],
                defaults={
                    'title': release['title'],
                    'message': release['message'],
                    'target_url': release['target_url'],
                },
            )
            state.last_event_key = release['event_key']
            state.save(update_fields=['last_event_key', 'checked_at'])

            if notification_created:
                created_count += 1
            _try_release_email(entry.user, notification)

        self.stdout.write(
            self.style.SUCCESS(
                f'Checked {checked_count} favorite title(s); created {created_count} notification(s).'
            )
        )
