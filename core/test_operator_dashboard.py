import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from content.models import EpgRefreshState
from core.models import SystemSettings


class OperatorDashboardTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username='operator-staff',
            password='test-password',
            is_staff=True,
        )

    def test_anonymous_operator_dashboard_requires_login(self):
        response = self.client.get(reverse('operator_dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_non_staff_user_cannot_open_operator_dashboard(self):
        user = get_user_model().objects.create_user(
            username='ordinary-viewer',
            password='test-password',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertEqual(response.status_code, 403)

    def test_staff_dashboard_shows_default_guest_configuration(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Operator dashboard')
        self.assertContains(response, '>aitv<', html=False)
        self.assertContains(response, '>US<', html=False)
        self.assertContains(response, '>Shown<', html=False)
        self.assertContains(response, 'Preview guest home')
        self.assertContains(response, 'Preview Live TV')
        self.assertContains(response, 'href="/?guest_preview=1"', html=False)
        self.assertContains(response, 'href="/live-tv/?guest_preview=1"', html=False)
        self.assertContains(response, 'data-copy-target="guest-home-url"', html=False)
        self.assertContains(response, 'data-copy-target="guest-live-tv-url"', html=False)
        self.assertContains(response, 'data-copy-status', html=False)
        self.assertContains(response, 'operator-dashboard', html=False)
        self.assertContains(response, '?v=1', html=False)
        self.assertNotContains(response, reverse('admin:core_systemsettings_add'))
        self.assertContains(response, 'Guest settings are read-only for your account.')
        self.assertContains(response, 'Detailed EPG diagnostics require additional operator permission.')
        self.assertContains(response, '>Operator<', html=False)

    def test_staff_dashboard_uses_configured_guest_settings_and_sanitized_health(self):
        self.staff.user_permissions.add(
            Permission.objects.get(codename='change_systemsettings'),
            Permission.objects.get(codename='view_epgrefreshstate'),
        )
        settings = SystemSettings.load()
        settings.site_name = 'Pine Ridge Guest TV'
        settings.default_region = 'CA'
        settings.show_guest_account_links = False
        settings.save()
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='CA',
            refreshed_at=timezone.now(),
            airing_count=14,
            attempted_at=timezone.now(),
            status=EpgRefreshState.Status.FAILURE,
            last_error='sensitive upstream response body',
        )
        self.client.force_login(self.staff)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertContains(response, 'Pine Ridge Guest TV')
        self.assertContains(response, '>CA<', html=False)
        self.assertContains(response, '>Hidden<', html=False)
        self.assertContains(response, 'FAILED')
        self.assertContains(response, '>14<', html=False)
        self.assertContains(
            response,
            reverse('admin:core_systemsettings_change', args=[1]),
        )
        self.assertContains(
            response,
            reverse('admin:content_epgrefreshstate_changelist'),
        )
        self.assertNotContains(response, 'sensitive upstream response body')

    @patch.dict(os.environ, {'EPG_REGIONS': 'US'})
    def test_dashboard_warns_when_guest_region_is_not_refreshed(self):
        settings = SystemSettings.load()
        settings.default_region = 'CA'
        settings.save()
        self.client.force_login(self.staff)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertContains(response, 'Live TV refresh is not configured for CA.')
        self.assertContains(response, 'EPG_REGIONS')

    @patch.dict(os.environ, {'EPG_REGIONS': 'US,CA'})
    def test_dashboard_does_not_warn_when_guest_region_is_configured(self):
        settings = SystemSettings.load()
        settings.default_region = 'CA'
        settings.save()
        self.client.force_login(self.staff)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertNotContains(response, 'Live TV refresh is not configured for CA.')

    @override_settings(ALLOWED_HOSTS=['guest.example.test'])
    def test_dashboard_builds_same_site_guest_launch_urls(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse('operator_dashboard'),
            secure=True,
            HTTP_HOST='guest.example.test',
        )

        self.assertEqual(
            response.context['operator_guest_home_url'],
            'https://guest.example.test/',
        )
        self.assertEqual(
            response.context['operator_guest_live_tv_url'],
            'https://guest.example.test/live-tv/',
        )
        self.assertContains(response, 'value="https://guest.example.test/"', html=False)
        self.assertContains(
            response,
            'value="https://guest.example.test/live-tv/"',
            html=False,
        )
        self.assertNotContains(response, 'http://guest.example.test/')

    @override_settings(ALLOWED_HOSTS=['guest.example.test'])
    def test_dashboard_builds_copyable_branded_guest_handoff_message(self):
        settings = SystemSettings.load()
        settings.site_name = 'Pine Ridge Guest TV'
        settings.welcome_message = 'Welcome! See what is on during your stay.'
        settings.save()
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse('operator_dashboard'),
            secure=True,
            HTTP_HOST='guest.example.test',
        )

        self.assertEqual(
            response.context['operator_guest_handoff_message'],
            (
                'Pine Ridge Guest TV\n'
                'Welcome! See what is on during your stay.\n'
                'Guest guide: https://guest.example.test/\n'
                'Live TV: https://guest.example.test/live-tv/'
            ),
        )
        self.assertContains(response, 'id="guest-handoff-message"', html=False)
        self.assertContains(
            response,
            'data-copy-target="guest-handoff-message"',
            html=False,
        )
        self.assertContains(response, 'Copy message')
        self.assertContains(response, 'Wi-Fi portal')

    def test_default_guest_handoff_message_omits_blank_welcome_line(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertEqual(
            response.context['operator_guest_handoff_message'],
            'aitv\nGuest guide: http://testserver/\nLive TV: http://testserver/live-tv/',
        )

    def test_staff_with_add_permission_can_open_initial_settings_admin(self):
        self.staff.user_permissions.add(
            Permission.objects.get(codename='add_systemsettings'),
        )
        self.client.force_login(self.staff)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertContains(response, reverse('admin:core_systemsettings_add'))
        self.assertNotContains(response, 'Guest settings are read-only for your account.')

    def test_staff_without_settings_permission_cannot_post_guest_settings(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('operator_dashboard'),
            {
                'action': 'guest_settings',
                'site_name': 'Unauthorized Property',
                'welcome_message': 'Should not save',
                'default_region': 'CA',
                'show_guest_account_links': 'on',
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(SystemSettings.objects.exists())

    def test_staff_with_add_permission_can_create_guest_settings_inline(self):
        self.staff.user_permissions.add(
            Permission.objects.get(codename='add_systemsettings'),
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('operator_dashboard'),
            {
                'action': 'guest_settings',
                'site_name': 'Harbor Guest TV',
                'welcome_message': 'Welcome to the harbor.',
                'default_region': 'CA',
            },
        )

        self.assertRedirects(response, reverse('operator_dashboard'))
        settings = SystemSettings.objects.get(pk=1)
        self.assertEqual(settings.site_name, 'Harbor Guest TV')
        self.assertEqual(settings.welcome_message, 'Welcome to the harbor.')
        self.assertEqual(settings.default_region, 'CA')
        self.assertFalse(settings.show_guest_account_links)

    def test_staff_with_change_permission_can_update_guest_settings_inline(self):
        settings = SystemSettings.load()
        settings.site_name = 'Old Property'
        settings.save()
        self.staff.user_permissions.add(
            Permission.objects.get(codename='change_systemsettings'),
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('operator_dashboard'),
            {
                'action': 'guest_settings',
                'site_name': 'Updated Property TV',
                'welcome_message': 'Updated welcome message.',
                'default_region': 'US',
                'show_guest_account_links': 'on',
            },
        )

        self.assertRedirects(response, reverse('operator_dashboard'))
        settings.refresh_from_db()
        self.assertEqual(settings.site_name, 'Updated Property TV')
        self.assertEqual(settings.welcome_message, 'Updated welcome message.')
        self.assertEqual(settings.default_region, 'US')
        self.assertTrue(settings.show_guest_account_links)

    def test_inline_guest_settings_reject_invalid_region(self):
        settings = SystemSettings.load()
        self.staff.user_permissions.add(
            Permission.objects.get(codename='change_systemsettings'),
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse('operator_dashboard'),
            {
                'action': 'guest_settings',
                'site_name': 'Invalid Region Property',
                'welcome_message': '',
                'default_region': 'ZZ',
                'show_guest_account_links': 'on',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select a valid choice.')
        settings.refresh_from_db()
        self.assertEqual(settings.default_region, 'US')

    @patch.dict(os.environ, {'EPG_REGIONS': 'US'})
    def test_default_dashboard_is_not_pilot_ready_without_saved_settings_or_guide(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertFalse(response.context['operator_pilot_ready'])
        checks = {
            item['label']: item['ready']
            for item in response.context['operator_readiness_checks']
        }
        self.assertFalse(checks['Guest settings saved'])
        self.assertTrue(checks['EPG region configured'])
        self.assertFalse(checks['Guide data healthy'])
        self.assertContains(response, 'Needs attention')
        self.assertContains(response, 'Action needed')

    @patch.dict(os.environ, {'EPG_REGIONS': 'US'})
    def test_dashboard_is_pilot_ready_when_required_location_checks_pass(self):
        SystemSettings.load()
        now = timezone.now()
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            refreshed_at=now,
            airing_count=21,
            attempted_at=now,
            status=EpgRefreshState.Status.SUCCESS,
            last_error='',
        )
        self.client.force_login(self.staff)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertTrue(response.context['operator_pilot_ready'])
        self.assertTrue(all(
            item['ready']
            for item in response.context['operator_readiness_checks']
        ))
        self.assertContains(response, 'Pilot readiness')

    @patch.dict(os.environ, {'EPG_REGIONS': 'US'})
    def test_failed_epg_keeps_pilot_readiness_degraded(self):
        SystemSettings.load()
        now = timezone.now()
        EpgRefreshState.objects.create(
            source='tvmaze',
            region='US',
            refreshed_at=now,
            airing_count=21,
            attempted_at=now,
            status=EpgRefreshState.Status.FAILURE,
            last_error='operator-only upstream detail',
        )
        self.client.force_login(self.staff)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertFalse(response.context['operator_pilot_ready'])
        checks = {
            item['label']: item['ready']
            for item in response.context['operator_readiness_checks']
        }
        self.assertFalse(checks['Guide data healthy'])
        self.assertContains(response, 'Guide health is failed')
        self.assertNotContains(response, 'operator-only upstream detail')
