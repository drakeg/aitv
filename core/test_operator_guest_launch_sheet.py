from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import SystemSettings


class OperatorGuestLaunchSheetTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username='launch-sheet-staff',
            password='test-password',
            is_staff=True,
        )

    def test_anonymous_launch_sheet_requires_login(self):
        response = self.client.get(reverse('operator_guest_launch_sheet'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_non_staff_user_cannot_open_launch_sheet_or_qr(self):
        user = get_user_model().objects.create_user(
            username='launch-sheet-viewer',
            password='test-password',
        )
        self.client.force_login(user)

        sheet = self.client.get(reverse('operator_guest_launch_sheet'))
        qr = self.client.get(reverse('operator_guest_qr', args=['home']))

        self.assertEqual(sheet.status_code, 403)
        self.assertEqual(qr.status_code, 403)

    @override_settings(ALLOWED_HOSTS=['guest.example.test'])
    def test_launch_sheet_uses_configured_branding_and_same_site_urls(self):
        settings = SystemSettings.load()
        settings.site_name = 'Pine Ridge Guest TV'
        settings.welcome_message = 'Scan to see what is on during your stay.'
        settings.save()
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse('operator_guest_launch_sheet'),
            secure=True,
            HTTP_HOST='guest.example.test',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pine Ridge Guest TV')
        self.assertContains(response, 'Scan to see what is on during your stay.')
        self.assertContains(response, 'https://guest.example.test/')
        self.assertContains(response, 'https://guest.example.test/live-tv/')
        self.assertContains(
            response,
            f'src="{reverse("operator_guest_qr", args=["home"])}"',
            html=False,
        )
        self.assertContains(
            response,
            f'src="{reverse("operator_guest_qr", args=["live-tv"])}"',
            html=False,
        )
        self.assertContains(response, 'data-print-launch-sheet', html=False)

    def test_dashboard_links_to_printable_launch_sheet(self):
        self.client.force_login(self.staff)

        response = self.client.get(reverse('operator_dashboard'))

        self.assertContains(response, 'Print guest launch sheet')
        self.assertContains(response, reverse('operator_guest_launch_sheet'))

    @override_settings(ALLOWED_HOSTS=['guest.example.test'])
    def test_qr_endpoints_return_distinct_private_svg_codes(self):
        self.client.force_login(self.staff)

        home = self.client.get(
            reverse('operator_guest_qr', args=['home']),
            secure=True,
            HTTP_HOST='guest.example.test',
        )
        live_tv = self.client.get(
            reverse('operator_guest_qr', args=['live-tv']),
            secure=True,
            HTTP_HOST='guest.example.test',
        )

        self.assertEqual(home.status_code, 200)
        self.assertEqual(live_tv.status_code, 200)
        self.assertEqual(home['Content-Type'], 'image/svg+xml; charset=utf-8')
        self.assertEqual(home['Cache-Control'], 'private, no-store')
        self.assertEqual(home['X-Content-Type-Options'], 'nosniff')
        self.assertIn(b'<svg', home.content)
        self.assertIn(b'<svg', live_tv.content)
        self.assertNotEqual(home.content, live_tv.content)

    def test_qr_endpoint_rejects_unknown_target(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse('operator_guest_qr', args=['external-url']),
        )

        self.assertEqual(response.status_code, 404)
