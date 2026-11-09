from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from backend.judge.models import Profile
from security.api_security.rate_limit import RateLimiter


class PublicProfilePrivacyTests(TestCase):
    def setUp(self):
        # The login limiter is process-wide; earlier suites' login POSTs would otherwise trigger 429 here.
        with RateLimiter._lock:
            RateLimiter._requests.clear()
        self.member = User.objects.create_user(
            username='member', email='private@example.com', password='secret123'
        )
        Profile.objects.get_or_create(user=self.member)
        self.staff = User.objects.create_user(
            username='staff', password='secret123', is_staff=True
        )
        Profile.objects.get_or_create(user=self.staff)
        self.client = APIClient()

    def test_public_list_and_detail_do_not_reveal_private_account_fields(self):
        listing = self.client.get('/api/v2/users')
        self.assertEqual(listing.status_code, 200)
        member = next(item for item in listing.json()['data']['objects']
                      if item['username'] == 'member')
        self.assertNotIn('email', member)
        self.assertNotIn('is_active', member)
        self.assertNotIn('is_staff', member)

        detail = self.client.get('/api/v2/user/member')
        self.assertEqual(detail.status_code, 200)
        self.assertNotIn('email', detail.json()['data']['object'])
        self.assertEqual(self.client.get('/api/v2/users?q=private@example.com')
                         .json()['data']['objects'], [])

    def test_owner_and_staff_can_read_private_account_fields(self):
        other = User.objects.create_user('other', password='secret123')
        self.client.force_authenticate(other)
        self.assertNotIn('email', self.client.get('/api/v2/user/member')
                         .json()['data']['object'])
        self.client.force_authenticate(self.member)
        self.assertEqual(self.client.get('/api/v2/user/member')
                         .json()['data']['object']['email'], 'private@example.com')
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get('/api/v2/user/member')
                         .json()['data']['object']['email'], 'private@example.com')
        self.assertEqual(len(self.client.get('/api/v2/users?q=private@example.com')
                             .json()['data']['objects']), 1)

    def test_inactive_user_cannot_login_with_email_or_case_insensitive_name(self):
        self.member.is_active = False
        self.member.save(update_fields=['is_active'])
        for identifier in ('private@example.com', 'MEMBER'):
            response = self.client.post('/api/v2/auth/login',
                                        {'username': identifier, 'password': 'secret123'},
                                        format='json')
            self.assertEqual(response.status_code, 401)
        self.assertFalse(Token.objects.filter(user=self.member).exists())

    def test_active_user_can_still_login_with_email(self):
        response = self.client.post('/api/v2/auth/login',
                                    {'username': 'private@example.com', 'password': 'secret123'},
                                    format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json()['data'])
