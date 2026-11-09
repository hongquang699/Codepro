from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, Client

from backend.judge.models import Profile, Problem, Language, Submission

class CodeProOJAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test_user', password='password123')
        self.profile = Profile.objects.create(user=self.user, rating=1600, display_rank='Expert')
        self.lang = Language.objects.create(key='CPP17', name='C++17', short_name='C++17', common_name='C++')
        self.problem = Problem.objects.create(
            code='TEST_SUM',
            name='Test Sum Problem',
            description='Calculate A + B',
            time_limit=1.0,
            memory_limit=65536,
            points=100.0,
            is_public=True
        )

    def test_get_problems(self):
        res = self.client.get('/api/v2/problems')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.json()['data']['objects']) >= 1)

    def test_get_problem_detail(self):
        res = self.client.get(f'/api/v2/problem/{self.problem.code}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['data']['object']['code'], 'TEST_SUM')

    def test_submit_code(self):
        data = {
            'problem': 'TEST_SUM',
            'language': 'CPP17',
            'user': 'someone_else',
            'source': '#include <iostream>\\nint main() { return 0; }'
        }
        anonymous = self.client.post('/api/v2/submit', data, content_type='application/json')
        self.assertEqual(anonymous.status_code, 401)
        self.client.force_login(self.user)
        with patch('backend.api.v2.views.grade_submission'):
            res = self.client.post('/api/v2/submit', data, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        self.assertIn('submission_id', res.json()['data'])
        submission = Submission.objects.get(pk=res.json()['data']['submission_id'])
        self.assertEqual(submission.user, self.profile)
        self.assertEqual(submission.status, 'QU')
        self.assertNotEqual(submission.result, 'AC')

    def test_get_users(self):
        res = self.client.get('/api/v2/users')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(any(u['username'] == 'test_user' for u in res.json()['data']['objects']))
