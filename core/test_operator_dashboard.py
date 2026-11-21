from django.contrib.auth import get_user_model
from django.test import TestCase
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
        self.assertContains(response, reverse('admin:core_systemsettings_add'))
        self.assertContains(response, '>Operator<', html=False)

    def test_staff_dashboard_uses_configured_guest_settings_and_sanitized_health(self):
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
