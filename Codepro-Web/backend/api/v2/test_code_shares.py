from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from backend.judge.models import CodeShare, Contest, ContestParticipation, ContestProblem, Problem, Profile


class CodeShareAPITests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user('owner', password='test-password')
        self.other = User.objects.create_user('other', password='test-password')
        self.admin = User.objects.create_user('admin', password='test-password', is_staff=True)
        self.problem = Problem.objects.create(code='SHARE_A', name='Share A', description='Test', is_public=True, status='published')
        self.client = APIClient()

    def test_owner_can_share_and_admin_can_revoke_without_other_user_writing(self):
        body = {'problem': 'SHARE_A', 'language': 'CPP17', 'source': 'int main() {}'}
        self.client.force_authenticate(self.owner)
        response = self.client.post('/api/v2/code-shares', body, format='json')
        self.assertEqual(response.status_code, 201)
        token = response.data['data']['token']
        self.assertEqual(len(token), 43)

        self.client.force_authenticate(user=None)
        public = self.client.get(f'/api/v2/code-share/{token}')
        self.assertEqual(public.status_code, 200)
        self.assertEqual(public.data['data']['source'], body['source'])

        self.client.force_authenticate(self.other)
        denied = self.client.put(f'/api/v2/code-share/{token}', {**body, 'source': 'changed'}, format='json')
        self.assertEqual(denied.status_code, 403)

        self.client.force_authenticate(self.owner)
        updated = self.client.put(f'/api/v2/code-share/{token}', {**body, 'source': 'new source'}, format='json')
        self.assertEqual(updated.status_code, 200)

        self.client.force_authenticate(self.admin)
        listed = self.client.get('/api/v2/code-shares')
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.data['data']['objects'][0]['owner'], 'owner')
        revoked = self.client.put(f'/api/v2/code-share/{token}', {'is_active': False}, format='json')
        self.assertEqual(revoked.status_code, 200)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(f'/api/v2/code-share/{token}').status_code, 404)

    def test_contest_share_requires_participation_and_expires(self):
        now = timezone.now()
        contest = Contest.objects.create(key='SHARE_TEST', name='Share test', start_time=now - timedelta(hours=1), end_time=now + timedelta(hours=1))
        ContestProblem.objects.create(contest=contest, problem=self.problem)
        body = {'problem': 'SHARE_A', 'contest': contest.key, 'language': 'CPP17', 'source': 'code'}
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post('/api/v2/code-shares', body, format='json').status_code, 400)
        profile, _ = Profile.objects.get_or_create(user=self.owner)
        ContestParticipation.objects.create(contest=contest, user=profile)
        response = self.client.post('/api/v2/code-shares', body, format='json')
        self.assertEqual(response.status_code, 201)
        token = response.data['data']['token']
        CodeShare.objects.filter(token=token).update(expires_at=now - timedelta(seconds=1))
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(f'/api/v2/code-share/{token}').status_code, 404)
