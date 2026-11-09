"""Object access checks for public profiles and admin-only edits."""

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from backend.judge.models import Profile


class UserAccessTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('profile_owner', email='private@example.test', password='password123')
        self.other = User.objects.create_user('profile_other', password='password123')
        Profile.objects.create(user=self.owner)
        Profile.objects.create(user=self.other)
        self.api = APIClient()

    def test_other_user_cannot_read_private_email_or_edit_profile(self):
        self.api.force_authenticate(user=self.other)
        url = '/api/v2/user/profile_owner'
        response = self.api.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('email', response.json()['data']['object'])

        response = self.api.put(url, {'about': 'tampered'}, format='json')
        self.assertEqual(response.status_code, 403)
