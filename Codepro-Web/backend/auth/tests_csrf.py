import json

from django.contrib.auth.models import User
from django.test import Client, TestCase

from backend.auth.services.session import create_auth_session, validate_auth_session


class CookieAuthCsrfTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='csrf_user', password='OldPassword123!')
        self.client = Client(enforce_csrf_checks=True)
        self.token, _ = create_auth_session(self.user, self.client.get('/api/v1/auth/me').wsgi_request)

    def test_cookie_change_password_requires_csrf_and_accepts_valid_token(self):
        self.client.cookies['cp_session'] = self.token
        payload = json.dumps({
            'current_password': 'OldPassword123!',
            'new_password': 'NewPassword123!',
            'new_password_confirm': 'NewPassword123!',
        })

        rejected = self.client.post('/api/v1/auth/change-password', payload,
                                    content_type='application/json')
        self.assertEqual(rejected.status_code, 403)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OldPassword123!'))

        self.assertEqual(self.client.get('/api/v1/auth/me').status_code, 200)
        csrf_token = self.client.cookies['csrftoken'].value
        accepted = self.client.post('/api/v1/auth/change-password', payload,
                                    content_type='application/json', HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(accepted.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))

    def test_bearer_only_client_does_not_need_csrf(self):
        response = self.client.post('/api/v1/auth/sessions/revoke-others',
                                    HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, 200)

    def test_cookie_session_changes_reject_missing_csrf(self):
        self.client.cookies['cp_session'] = self.token
        for path in ('/api/v1/auth/logout', '/api/v1/auth/sessions/revoke-others',
                     '/api/v1/auth/2fa/disable'):
            response = self.client.post(path, '{}', content_type='application/json')
            self.assertEqual(response.status_code, 403, path)
        self.assertEqual(validate_auth_session(self.token), self.user)

    def test_logout_accepts_valid_csrf(self):
        self.client.cookies['cp_session'] = self.token
        self.client.get('/api/v1/auth/me')
        csrf_token = self.client.cookies['csrftoken'].value
        response = self.client.post('/api/v1/auth/logout', HTTP_X_CSRFTOKEN=csrf_token)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(validate_auth_session(self.token))

    def test_cookie_request_rejects_foreign_origin_even_with_token(self):
        self.client.cookies['cp_session'] = self.token
        self.client.get('/api/v1/auth/me')
        csrf_token = self.client.cookies['csrftoken'].value
        response = self.client.post('/api/v1/auth/sessions/revoke-others',
                                    HTTP_X_CSRFTOKEN=csrf_token,
                                    HTTP_ORIGIN='https://untrusted.example')
        self.assertEqual(response.status_code, 403)
