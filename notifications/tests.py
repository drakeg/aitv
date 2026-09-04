from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from content.models import ContentItem, DiscoveryPreference
from notifications.models import ReleaseNotification, ReleaseWatchState
from watchlist.models import Watchlist


class ReleaseNotificationWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='viewer',
            password='test-password',
            email='viewer@example.com',
        )
        DiscoveryPreference.objects.create(
            user=self.user,
            notify_new_releases=True,
        )
        self.content = ContentItem.objects.create(
            title='Example Series',
            url='https://www.themoviedb.org/tv/42',
            genre='Drama',
            source_type='tmdb',
            content_type='tv',
            external_source='tmdb',
            external_id='42',
        )
        Watchlist.objects.create(user=self.user, content=self.content, is_favorite=True)

    @patch('notifications.management.commands.check_release_notifications.send_release_email')
    @patch('notifications.management.commands.check_release_notifications.fetch_latest_release')
    def test_first_scan_establishes_baseline_without_notification(self, mock_fetch, mock_email):
        mock_fetch.return_value = {
            'event_key': 'tmdb-tv:42:S1 E2:2026-09-01',
            'title': 'New episode: Example Series',
            'message': 'Example Series released S1 E2 on 2026-09-01.',
            'target_url': self.content.url,
        }

        call_command('check_release_notifications', stdout=StringIO())

        state = ReleaseWatchState.objects.get(user=self.user, content=self.content)
        self.assertEqual(state.last_event_key, mock_fetch.return_value['event_key'])
        self.assertFalse(ReleaseNotification.objects.exists())
        mock_email.assert_not_called()

    @patch('notifications.management.commands.check_release_notifications.send_release_email')
    @patch('notifications.management.commands.check_release_notifications.fetch_latest_release')
    def test_new_episode_creates_one_notification_and_email_attempt(self, mock_fetch, mock_email):
        ReleaseWatchState.objects.create(
            user=self.user,
            content=self.content,
            last_event_key='tmdb-tv:42:S1 E1:2026-08-25',
        )
        mock_fetch.return_value = {
            'event_key': 'tmdb-tv:42:S1 E2:2026-09-01',
            'title': 'New episode: Example Series',
            'message': 'Example Series released S1 E2 on 2026-09-01.',
            'target_url': self.content.url,
        }

        call_command('check_release_notifications', stdout=StringIO())
        call_command('check_release_notifications', stdout=StringIO())

        self.assertEqual(ReleaseNotification.objects.count(), 1)
        notification = ReleaseNotification.objects.get()
        self.assertEqual(notification.event_key, mock_fetch.return_value['event_key'])
        mock_email.assert_called_once_with(self.user, notification)

    @patch('notifications.management.commands.check_release_notifications.fetch_latest_release')
    def test_nonfavorite_saved_title_is_not_checked(self, mock_fetch):
        Watchlist.objects.filter(user=self.user, content=self.content).update(is_favorite=False)

        call_command('check_release_notifications', stdout=StringIO())

        mock_fetch.assert_not_called()
        self.assertFalse(ReleaseWatchState.objects.exists())

    @patch('notifications.management.commands.check_release_notifications.fetch_latest_release')
    def test_opted_out_user_is_not_checked(self, mock_fetch):
        preference = DiscoveryPreference.objects.get(user=self.user)
        preference.notify_new_releases = False
        preference.save(update_fields=['notify_new_releases'])

        call_command('check_release_notifications', stdout=StringIO())

        mock_fetch.assert_not_called()
        self.assertFalse(ReleaseWatchState.objects.exists())

    def test_inbox_requires_login_and_marks_only_own_notification_read(self):
        notification = ReleaseNotification.objects.create(
            user=self.user,
            content=self.content,
            event_key='event-1',
            title='New episode',
            message='Episode available.',
            target_url=self.content.url,
        )
        self.assertEqual(self.client.get(reverse('notifications:inbox')).status_code, 302)

        self.client.force_login(self.user)
        response = self.client.get(reverse('notifications:inbox'))
        self.assertContains(response, 'New episode')
        self.assertContains(response, 'Episode available.')

        response = self.client.post(reverse('notifications:mark_read', args=[notification.id]))
        self.assertRedirects(response, reverse('notifications:inbox'))
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)
