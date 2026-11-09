import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'judge-server'))

from api import JudgeApiRouter
from authentication import Authenticator
from heartbeat import HeartbeatManager
from dispatcher.queue import SubmissionQueue


class AdminControlTests(unittest.TestCase):
    def setUp(self):
        self.router = JudgeApiRouter(Authenticator('test-secret'), HeartbeatManager(), SubmissionQueue(), {})
        self.headers = {'Authorization': 'Bearer test-secret'}

    def call(self, method, path, body=None, authorized=True):
        return self.router.handle(method, path, self.headers if authorized else {}, json.dumps(body or {}).encode())

    def test_queue_pause_resume_and_cancel(self):
        code, _ = self.call('POST', '/api/v1/submissions', {'job_id': 'job-1', 'problem_code': 'SUM'})
        self.assertEqual(code, 202)
        self.assertEqual(self.call('POST', '/api/v1/admin/queue/pause')[0], 200)
        self.assertIsNone(self.call('GET', '/api/v1/jobs/poll?worker_id=worker-1')[1]['job'])
        self.assertEqual(self.call('POST', '/api/v1/admin/queue/resume')[0], 200)
        self.assertEqual(self.call('POST', '/api/v1/admin/queue/job-1/cancel')[0], 200)
        self.assertIsNone(self.call('GET', '/api/v1/jobs/poll?worker_id=worker-1')[1]['job'])

    def test_disabled_worker_does_not_receive_jobs(self):
        self.router.heartbeat.record_heartbeat('worker-1')
        self.call('POST', '/api/v1/submissions', {'job_id': 'job-2', 'problem_code': 'SUM'})
        self.assertEqual(self.call('POST', '/api/v1/admin/workers/worker-1/disable')[0], 200)
        self.assertIsNone(self.call('GET', '/api/v1/jobs/poll?worker_id=worker-1')[1]['job'])
        self.assertEqual(self.call('POST', '/api/v1/admin/workers/worker-1/enable')[0], 200)
        self.assertEqual(self.call('GET', '/api/v1/jobs/poll?worker_id=worker-1')[1]['job']['job_id'], 'job-2')
        self.assertEqual(self.call('POST', '/api/v1/admin/queue/job-2/cancel')[0], 409)

    def test_admin_controls_require_manager_token(self):
        self.assertEqual(self.call('POST', '/api/v1/admin/queue/pause', authorized=False)[0], 401)
        self.assertEqual(self.call('GET', '/api/v1/admin/queue', authorized=False)[0], 401)

    def test_restart_is_delivered_to_worker_on_next_poll(self):
        self.router.heartbeat.record_heartbeat('worker-1')
        code, data = self.call('POST', '/api/v1/admin/workers/worker-1/restart')
        self.assertEqual(code, 202)
        self.assertEqual(data['status'], 'restart scheduled after current job')
        self.assertEqual(self.call('GET', '/api/v1/jobs/poll?worker_id=worker-1')[1]['command'], 'restart')
        self.assertEqual(self.router.worker_modes['worker-1'], 'enabled')

    def test_submission_limits_are_enforced_by_manager(self):
        self.router.limits = {'execution': {'max_memory_limit_mb': 512, 'min_memory_limit_mb': 16,
                                            'max_time_limit_sec': 5, 'min_time_limit_sec': 0.1},
                              'storage': {'max_source_size_bytes': 10}}
        self.assertEqual(self.call('POST', '/api/v1/submissions', {'job_id': 'too-big', 'source_code': 'x'*11})[0], 400)
        code, _ = self.call('POST', '/api/v1/submissions',
                            {'job_id': 'bounded', 'source_code': 'x', 'memory_limit': 99999, 'time_limit': 99})
        self.assertEqual(code, 202)
        job = self.call('GET', '/api/v1/jobs/poll?worker_id=worker-1')[1]['job']
        self.assertEqual(job['memory_limit'], 512)
        self.assertEqual(job['time_limit'], 5)

    def test_system_error_appears_in_failed_queue(self):
        self.call('POST', '/api/v1/submissions', {'job_id': 'job-error', 'source_code': 'x'})
        self.call('GET', '/api/v1/jobs/poll?worker_id=worker-1')
        self.call('POST', '/api/v1/results', {'job_id': 'job-error', 'verdict': 'SE'})
        data = self.call('GET', '/api/v1/admin/queue')[1]
        self.assertEqual(data['results'][0]['status'], 'Failed')
        self.assertEqual(data['results'][0]['assigned_worker'], 'worker-1')


if __name__ == '__main__':
    unittest.main()
