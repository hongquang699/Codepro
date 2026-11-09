from unittest.mock import patch
from django.contrib.auth.models import Group, User
from django.test import Client, RequestFactory, TestCase
from rest_framework.test import APIClient
from backend.judge.models import JudgeLog, Language, Problem
from backend.auth.services.session import create_auth_session


class JudgeAdminAccessTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('judge-admin', password='pass', is_staff=True)
        self.user = User.objects.create_user('contestant', password='pass')
        self.api = APIClient()

    def test_anonymous_and_contestant_cannot_read_or_mutate(self):
        for method, path in [('get', '/api/v1/admin/judge/workers'),
                             ('post', '/api/v1/admin/judge/queue/pause')]:
            response = getattr(self.api, method)(path)
            self.assertIn(response.status_code, (401, 403))
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.get('/api/v1/admin/judge/workers').status_code, 403)
        self.assertEqual(self.api.post('/api/v1/admin/judge/queue/pause').status_code, 403)
        self.assertEqual(JudgeLog.objects.count(), 0)

    def test_judge_manager_group_can_read(self):
        group = Group.objects.create(name='judge_manager')
        self.user.groups.add(group)
        self.api.force_authenticate(self.user)
        self.assertEqual(self.api.get('/api/v1/admin/judge/languages').status_code, 200)

    @patch('backend.judge.api.admin_views.call_manager')
    def test_staff_queue_action_is_forwarded_and_audited(self, call_manager):
        call_manager.return_value = {'paused': True}
        self.api.force_authenticate(self.staff)
        response = self.api.post('/api/v1/admin/judge/queue/pause')
        self.assertEqual(response.status_code, 200)
        call_manager.assert_called_once_with('admin/queue/pause', 'POST')
        self.assertEqual(JudgeLog.objects.get().action, 'queue.pause')

    def test_page_requires_judge_role(self):
        client = Client()
        self.assertEqual(client.get('/internal/judge-admin-page').status_code, 302)
        client.force_login(self.user)
        self.assertEqual(client.get('/internal/judge-admin-page').status_code, 403)
        client.force_login(self.staff)
        self.assertEqual(client.get('/internal/judge-admin-page').status_code, 200)

    @patch('backend.judge.api.admin_views.call_manager')
    def test_cookie_session_requires_csrf_for_actions(self, call_manager):
        raw, _ = create_auth_session(self.staff, RequestFactory().get('/'))
        client = Client(enforce_csrf_checks=True)
        client.cookies['cp_session'] = raw
        self.assertEqual(client.get('/api/v1/admin/judge/languages').status_code, 200)
        self.assertEqual(client.post('/api/v1/admin/judge/queue/pause').status_code, 403)
        call_manager.return_value = {'paused': True}
        token = client.cookies['csrftoken'].value
        self.assertEqual(client.post('/api/v1/admin/judge/queue/pause', HTTP_X_CSRFTOKEN=token).status_code, 200)

    @patch('backend.judge.api.admin_views.call_manager')
    def test_test_run_only_enqueues_on_manager(self, call_manager):
        Problem.objects.create(code='SUM', name='Sum', description='Add', memory_limit=262144)
        Language.objects.create(key='PY3', name='Python 3', short_name='Python', common_name='Python')
        call_manager.return_value = {'job_id': 'admin_test_1'}
        self.api.force_authenticate(self.staff)
        response = self.api.post('/api/v1/admin/judge/test/run',
                                 {'problem': 'SUM', 'language': 'PY3', 'source': 'print(1)'}, format='json')
        self.assertEqual(response.status_code, 202)
        args = call_manager.call_args.args
        self.assertEqual(args[:2], ('submissions', 'POST'))
        self.assertEqual(args[2]['memory_limit'], 256)
        self.assertEqual(JudgeLog.objects.get().action, 'test.run')
