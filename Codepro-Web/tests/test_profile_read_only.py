from django.contrib.auth.models import User
from django.test import TestCase

from backend.users.models import UserProfile, UserRating, UserStatistics


class ProfileReadOnlyTests(TestCase):
    def test_profile_get_does_not_create_or_update_cache_rows(self):
        user = User.objects.create_user(username='profile_reader', password='test-password')

        for _ in range(2):
            response = self.client.get('/api/v1/users/profile_reader')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['profile']['username'], user.username)

        self.assertFalse(UserProfile.objects.filter(user=user).exists())
        self.assertFalse(UserRating.objects.filter(user=user).exists())
        self.assertFalse(UserStatistics.objects.filter(user=user).exists())
