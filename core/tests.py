from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AuthenticationFlowTests(TestCase):
    def test_login_page_is_available(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in')

    def test_registration_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'newviewer',
                'password1': 'A-strong-test-password-123!',
                'password2': 'A-strong-test-password-123!',
            },
        )

        self.assertRedirects(response, reverse('home'))
        self.assertTrue(get_user_model().objects.filter(username='newviewer').exists())
        self.assertEqual(self.client.session.get('_auth_user_id'), str(get_user_model().objects.get(username='newviewer').pk))

    def test_logout_requires_post_and_logs_user_out(self):
        user = get_user_model().objects.create_user(username='viewer', password='test-password')
        self.client.force_login(user)

        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)
