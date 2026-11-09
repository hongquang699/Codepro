import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from backend.auth.models.login_attempt import LoginAttempt
from backend.auth.services.session import validate_auth_session


class LoginTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'logintester'
        self.email = 'logintester@example.com'
        self.password = 'SecurePass123!'
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password
        )

    def test_login_successful_with_username(self):
        res = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': self.username, 'password': self.password}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['authenticated'])
        self.assertEqual(data['user']['username'], self.username)
        self.assertIn('cp_session', res.cookies)

        # Validate session from cookie
        session_token = res.cookies['cp_session'].value
        user = validate_auth_session(session_token)
        self.assertEqual(user, self.user)

    def test_login_successful_with_email(self):
        res = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': self.email, 'password': self.password}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['authenticated'])

    def test_login_wrong_password(self):
        res = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': self.username, 'password': 'WrongPassword999'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertFalse(data['authenticated'])

    def test_brute_force_lockout_after_five_attempts(self):
        for _ in range(5):
            self.client.post(
                '/api/v1/auth/login',
                data=json.dumps({'username': self.username, 'password': 'WrongPassword'}),
                content_type='application/json'
            )

        # 6th attempt should return lockout message
        res = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': self.username, 'password': self.password}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertIn('khóa', data['message'].lower())

    def test_logout(self):
        User.objects.create_user(username='logout_test_user', password='Password123!')
        login_res = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': 'logout_test_user', 'password': 'Password123!'}),
            content_type='application/json',
            REMOTE_ADDR='127.0.0.88'
        )
        self.assertEqual(login_res.status_code, 200)
        token = login_res.cookies['cp_session'].value

        # Logout
        logout_res = self.client.post('/api/v1/auth/logout')
        self.assertEqual(logout_res.status_code, 200)

        # Session should be revoked
        user_after = validate_auth_session(token)
        self.assertIsNone(user_after)

    def test_admin_login_blocked_from_unauthorized_ip(self):
        admin_user = User.objects.create_superuser(
            username='system_admin',
            email='admin@example.com',
            password='AdminSecretPassword123!'
        )
        res = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': 'system_admin', 'password': 'AdminSecretPassword123!'}),
            content_type='application/json',
            REMOTE_ADDR='203.0.113.199'
        )
        self.assertEqual(res.status_code, 403)
        data = res.json()
        self.assertFalse(data['authenticated'])
        self.assertEqual(data.get('error_code'), 'ADMIN_IP_RESTRICTED')
        self.assertIn('IP được ủy quyền', data['message'])

    def test_admin_login_allowed_from_whitelisted_ip(self):
        admin_user = User.objects.create_superuser(
            username='whitelisted_admin',
            email='wadmin@example.com',
            password='AdminSecretPassword123!'
        )
        res = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': 'whitelisted_admin', 'password': 'AdminSecretPassword123!'}),
            content_type='application/json',
            REMOTE_ADDR='127.0.0.1'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['authenticated'])
        self.assertTrue(data['user']['is_admin'])

    def test_regular_user_allowed_from_external_ip(self):
        # Normal users are not subject to admin IP restriction
        res = self.client.post(
            '/api/v1/auth/login',
            data=json.dumps({'username': self.username, 'password': self.password}),
            content_type='application/json',
            REMOTE_ADDR='198.51.100.42'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['authenticated'])

