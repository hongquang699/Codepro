"""API regression tests for encrypted testcase authoring paths."""

import base64
import io
import os
import tempfile
import zipfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from backend.judge.models import Contest, Problem
from security.encryption import file_cipher


class EncryptedTestcaseAPITests(TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        settings_override = override_settings(DMOJ_PROBLEM_DATA_ROOT=str(self.root))
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        key_override = patch.dict(os.environ, {
            'TESTCASE_ENCRYPTION_KEY': base64.b64encode(os.urandom(32)).decode('ascii')
        })
        key_override.start()
        self.addCleanup(key_override.stop)

        self.staff = User.objects.create_user('api_staff', password='password123', is_staff=True)
        self.problem = Problem.objects.create(code='ENC_TEST', name='Encrypted testcase', description='test')
        self.api = APIClient()
        self.api.force_authenticate(user=self.staff)
        self.cases = self.root / self.problem.code / 'cases'

    def assert_case(self, case_id, input_bytes, output_bytes):
        for extension, expected in (('in', input_bytes), ('out', output_bytes)):
            path = self.cases / f'{case_id}.{extension}'
            self.assertTrue(file_cipher.is_encrypted(path))
            self.assertNotIn(expected, path.read_bytes())
            self.assertEqual(file_cipher.read_file(path), expected)

    def test_v1_create_and_list(self):
        url = f'/api/v1/problems/{self.problem.code}/testcases'
        created = self.api.post(url, {'id': '01', 'input': '1 2\n', 'output': '3\n'}, format='json')
        self.assertEqual(created.status_code, 201, created.content)
        self.assert_case('01', b'1 2\n', b'3\n')
        listed = self.api.get(url)
        self.assertEqual(listed.status_code, 200, listed.content)
        self.assertEqual(listed.json()['data']['testcases'][0]['in_preview'], '1 2\n')

    def test_v2_create_list_and_zip_upload(self):
        url = f'/api/v2/problem/{self.problem.code}/testcases'
        created = self.api.post(url, {'id': '02', 'input': '4 5\n', 'output': '9\n'}, format='json')
        self.assertEqual(created.status_code, 201, created.content)
        self.assert_case('02', b'4 5\n', b'9\n')

        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as zipped:
            zipped.writestr('03.in', '6 7\n')
            zipped.writestr('03.out', '13\n')
        uploaded = self.api.post(f'{url}/upload', {
            'file': SimpleUploadedFile('testcases.zip', archive.getvalue(), content_type='application/zip')
        }, format='multipart')
        self.assertEqual(uploaded.status_code, 200, uploaded.content)
        self.assert_case('03', b'6 7\n', b'13\n')

        listed = self.api.get(url)
        self.assertEqual(listed.status_code, 200, listed.content)
        cases = {case['id']: case for case in listed.json()['data']['testcases']}
        self.assertEqual(cases['02']['input_size'], 4)
        self.assertEqual(cases['03']['output_size'], 3)

    def test_v1_zip_upload(self):
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as zipped:
            zipped.writestr('05.in', '10 11\n')
            zipped.writestr('05.out', '21\n')
        url = f'/api/v1/problems/{self.problem.code}/testcases/upload'
        uploaded = self.api.post(url, {
            'file': SimpleUploadedFile('testcases.zip', archive.getvalue(), content_type='application/zip')
        }, format='multipart')
        self.assertEqual(uploaded.status_code, 200, uploaded.content)
        self.assert_case('05', b'10 11\n', b'21\n')

    def test_upload_rejects_disguised_and_duplicate_zip_without_writing_cases(self):
        bad_file = SimpleUploadedFile('testcases.zip', b'not a ZIP', content_type='application/zip')
        url_v1 = f'/api/v1/problems/{self.problem.code}/testcases/upload'
        response = self.api.post(url_v1, {'file': bad_file}, format='multipart')
        self.assertEqual(response.status_code, 400)

        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as zipped:
            zipped.writestr('07.in', 'first')
            zipped.writestr('07.in', 'second')
        url_v2 = f'/api/v2/problem/{self.problem.code}/testcases/upload'
        response = self.api.post(url_v2, {
            'file': SimpleUploadedFile('testcases.zip', archive.getvalue(), content_type='application/zip')
        }, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertFalse((self.cases / '07.in').exists())

    def test_contest_admin_create_list_and_reject_path(self):
        now = timezone.now()
        contest = Contest.objects.create(key='ENC_CONTEST', name='Encryption test',
                                         start_time=now, end_time=now + timedelta(hours=1))
        url = f'/api/v1/contest-admin/contests/{contest.key}/problems/{self.problem.code}/testcases'
        rejected = self.api.post(url, {'id': '../escape', 'input': 'x', 'output': 'y'}, format='json')
        self.assertEqual(rejected.status_code, 400, rejected.content)
        created = self.api.post(url, {'id': '04', 'input': '8\n', 'output': '8\n'}, format='json')
        self.assertEqual(created.status_code, 201, created.content)
        self.assert_case('04', b'8\n', b'8\n')
        listed = self.api.get(url)
        self.assertEqual(listed.status_code, 200, listed.content)
        self.assertEqual(listed.json()['data'][0]['input_size'], 2)
