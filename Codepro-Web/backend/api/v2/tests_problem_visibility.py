from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from backend.judge.models import Language, Problem, Profile


class ProblemVisibilityTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('visibility_admin', is_staff=True)
        self.staff_api = APIClient()
        self.staff_api.force_authenticate(user=self.staff)
        self.public_api = APIClient()
        self.problem = Problem.objects.create(
            code='VISIBILITY_TEST', name='Visibility test', description='Test',
            status='published', is_public=True,
        )

    def test_admin_can_hide_and_republish_without_losing_problem(self):
        hidden = self.staff_api.post('/api/v1/problems/VISIBILITY_TEST/unpublish')
        self.assertEqual(hidden.status_code, 200)
        self.problem.refresh_from_db()
        self.assertEqual(self.problem.status, 'ready')
        self.assertFalse(self.problem.is_public)

        public_list = self.public_api.get('/api/v2/problems')
        self.assertEqual(public_list.status_code, 200)
        self.assertEqual(public_list.data['data']['objects'], [])
        self.assertEqual(self.public_api.get('/api/v2/problems?all=1').data['data']['objects'], [])
        self.assertEqual(self.public_api.get('/api/v2/problem/VISIBILITY_TEST').status_code, 403)

        admin_list = self.staff_api.get('/api/v2/problems?all=1')
        self.assertEqual(admin_list.status_code, 200)
        self.assertEqual(admin_list.data['data']['objects'][0]['status'], 'ready')
        self.assertFalse(admin_list.data['data']['objects'][0]['is_public'])

        with patch('backend.api.v1.problems.views.pkg.check_publish_readiness', return_value={'ready': True}):
            published = self.staff_api.post('/api/v1/problems/VISIBILITY_TEST/publish')
        self.assertEqual(published.status_code, 200)
        self.problem.refresh_from_db()
        self.assertEqual(self.problem.status, 'published')
        self.assertTrue(self.problem.is_public)
        self.assertEqual(self.public_api.get('/api/v2/problems').data['data']['objects'][0]['code'], self.problem.code)

    def test_nonstaff_cannot_change_visibility(self):
        user_api = APIClient()
        user_api.force_authenticate(user=User.objects.create_user('ordinary_user'))
        self.assertEqual(user_api.post('/api/v1/problems/VISIBILITY_TEST/unpublish').status_code, 403)
        self.problem.refresh_from_db()
        self.assertTrue(self.problem.is_public)

    def test_only_admin_can_submit_hidden_problem(self):
        self.problem.is_public = False
        self.problem.status = 'ready'
        self.problem.save(update_fields=['is_public', 'status'])
        Profile.objects.create(user=self.staff)
        regular = User.objects.create_user('hidden_regular')
        Profile.objects.create(user=regular)
        Language.objects.create(key='PY3', name='Python 3', short_name='Python',
                                common_name='Python', is_active=True)
        payload = {'problem': self.problem.code, 'language': 'PY3', 'source': 'print(1)'}
        regular_api = APIClient()
        regular_api.force_authenticate(user=regular)

        self.assertEqual(regular_api.get('/api/v2/problem/VISIBILITY_TEST').status_code, 403)
        self.assertEqual(regular_api.post('/api/v2/submit', payload).status_code, 403)
        self.assertEqual(self.staff_api.get('/api/v2/problem/VISIBILITY_TEST').status_code, 200)
        with patch('backend.api.v2.views.grade_submission'):
            self.assertEqual(self.staff_api.post('/api/v2/submit', payload).status_code, 201)
