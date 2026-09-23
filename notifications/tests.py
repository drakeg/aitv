from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

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
        mock_email.return_value = True
        call_command('check_release_notifications', stdout=StringIO())
        call_command('check_release_notifications', stdout=StringIO())
        self.assertEqual(ReleaseNotification.objects.count(), 1)
        notification = ReleaseNotification.objects.get()
        self.assertEqual(notification.event_key, mock_fetch.return_value['event_key'])
        self.assertIsNotNone(notification.email_sent_at)
        mock_email.assert_called_once_with(self.user, notification)

    @patch('notifications.management.commands.check_release_notifications.send_release_email')
    @patch('notifications.management.commands.check_release_notifications.fetch_latest_release')
    def test_failed_release_email_is_retried_without_duplicate_notification(self, mock_fetch, mock_email):
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
        mock_email.side_effect = [RuntimeError('smtp temporarily unavailable'), True]

        call_command('check_release_notifications', stdout=StringIO())
        notification = ReleaseNotification.objects.get()
        self.assertIsNone(notification.email_sent_at)

        call_command('check_release_notifications', stdout=StringIO())
        notification.refresh_from_db()

        self.assertEqual(ReleaseNotification.objects.count(), 1)
        self.assertIsNotNone(notification.email_sent_at)
        self.assertEqual(mock_email.call_count, 2)

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

    def test_mark_read_preserves_safe_inbox_page_and_rejects_external_redirect(self):
        notification = ReleaseNotification.objects.create(
            user=self.user,
            content=self.content,
            event_key='page-preserve',
            title='Page-preserved notification',
            message='Keep the current page.',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('notifications:mark_read', args=[notification.id]),
            {'next': f"{reverse('notifications:inbox')}?page=2"},
        )
        self.assertRedirects(
            response,
            f"{reverse('notifications:inbox')}?page=2",
            fetch_redirect_response=False,
        )
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)

        notification.read_at = None
        notification.save(update_fields=['read_at'])
        response = self.client.post(
            reverse('notifications:mark_read', args=[notification.id]),
            {'next': 'https://evil.example/phishing'},
        )
        self.assertRedirects(response, reverse('notifications:inbox'))

    def test_mark_all_read_preserves_safe_inbox_page_and_rejects_external_redirect(self):
        ReleaseNotification.objects.create(
            user=self.user,
            content=self.content,
            event_key='mark-all-page',
            title='Unread page notification',
            message='Mark all while staying here.',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('notifications:mark_all_read'),
            {'next': f"{reverse('notifications:inbox')}?page=2"},
        )
        self.assertRedirects(
            response,
            f"{reverse('notifications:inbox')}?page=2",
            fetch_redirect_response=False,
        )
        self.assertFalse(
            ReleaseNotification.objects.filter(user=self.user, read_at__isnull=True).exists()
        )

        response = self.client.post(
            reverse('notifications:mark_all_read'),
            {'next': 'https://evil.example/phishing'},
        )
        self.assertRedirects(response, reverse('notifications:inbox'))

    def test_inbox_reuses_navigation_unread_count(self):
        ReleaseNotification.objects.create(
            user=self.user,
            content=self.content,
            event_key='unread-inbox',
            title='Unread inbox notification',
            message='Unread notification.',
        )
        ReleaseNotification.objects.create(
            user=self.user,
            content=self.content,
            event_key='read-inbox',
            title='Read inbox notification',
            message='Read notification.',
            read_at=timezone.now(),
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('notifications:inbox'))
        self.assertEqual(response.context['unread_notification_count'], 1)
        self.assertNotIn('unread_count', response.context)
        self.assertContains(response, 'Mark all read')
        self.assertContains(response, '>1</span>', html=False)

    def test_inbox_paginates_notifications_and_handles_invalid_page(self):
        for index in range(30):
            ReleaseNotification.objects.create(
                user=self.user,
                content=self.content,
                event_key=f'page-{index}',
                title=f'Notification {index}',
                message=f'Page notification {index}.',
            )
        self.client.force_login(self.user)

        first_page = self.client.get(reverse('notifications:inbox'))
        self.assertEqual(len(first_page.context['notifications']), 25)
        self.assertEqual(first_page.context['page_obj'].number, 1)
        self.assertEqual(first_page.context['page_obj'].paginator.count, 30)
        self.assertContains(first_page, 'aria-current="page"')
        self.assertContains(first_page, '?page=2')

        second_page = self.client.get(reverse('notifications:inbox'), {'page': 2})
        self.assertEqual(len(second_page.context['notifications']), 5)
        self.assertEqual(second_page.context['page_obj'].number, 2)
        self.assertContains(second_page, 'aria-current="page"')

        invalid_page = self.client.get(reverse('notifications:inbox'), {'page': 'not-a-number'})
        self.assertEqual(invalid_page.context['page_obj'].number, 1)

        past_end = self.client.get(reverse('notifications:inbox'), {'page': 999})
        self.assertEqual(past_end.context['page_obj'].number, 2)

    def test_inbox_shows_elided_direct_page_navigation_for_long_history(self):
        for index in range(400):
            ReleaseNotification.objects.create(
                user=self.user,
                content=self.content,
                event_key=f'long-page-{index}',
                title=f'Long history {index}',
                message=f'Long notification {index}.',
            )
        self.client.force_login(self.user)

        response = self.client.get(reverse('notifications:inbox'), {'page': 8})
        self.assertEqual(response.context['page_obj'].number, 8)
        self.assertEqual(response.context['page_obj'].paginator.num_pages, 16)
        self.assertContains(response, 'aria-current="page"')
        self.assertContains(response, '?page=1')
        self.assertContains(response, '?page=7')
        self.assertContains(response, '?page=9')
        self.assertContains(response, '?page=16')
        self.assertContains(response, '…')

    @patch('core.views.fetch_free_archive_movies', return_value=[])
    @patch('core.views.fetch_popular_tv', return_value=[])
    @patch('core.views.fetch_tv_on_the_air', return_value=[])
    @patch('core.views.fetch_trending_movies', return_value=[])
    @patch('core.views.fetch_trending_tv', return_value=[])
    @patch('core.views.fetch_live_tv_schedule', return_value=[])
    def test_navigation_shows_only_unread_notification_count(self, *_mocks):
        ReleaseNotification.objects.create(
            user=self.user,
            content=self.content,
            event_key='unread',
            title='Unread',
            message='Unread notification.',
        )
        ReleaseNotification.objects.create(
            user=self.user,
            content=self.content,
            event_key='read',
            title='Read',
            message='Read notification.',
            read_at=timezone.now(),
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Notifications')
        self.assertContains(response, '>1</span>', html=False)
        self.assertContains(response, '🎬 aitv')
