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

    def test_staff_with_add_permission_can_open_initial_settings_admin(self):
        self.staff.user_permissions.add(
            Permission.objects.get(codename='add_systemsettings'),
        )
        self.client.force_login(self.staff)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertContains(response, reverse('admin:core_systemsettings_add'))
        self.assertNotContains(response, 'Guest settings are read-only for your account.')
