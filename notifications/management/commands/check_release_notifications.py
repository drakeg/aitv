from django.core.management.base import BaseCommand

from content.models import DiscoveryPreference
from notifications.models import ReleaseNotification, ReleaseWatchState
from notifications.services import fetch_latest_release, send_release_email
from watchlist.models import Watchlist


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
                send_release_email(entry.user, notification)

        self.stdout.write(
            self.style.SUCCESS(
                f'Checked {checked_count} favorite title(s); created {created_count} notification(s).'
            )
        )
