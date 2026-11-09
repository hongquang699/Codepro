import json
import tempfile
from datetime import timedelta
from pathlib import Path
from zipfile import ZipFile

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from backend.judge.models import Contest, ContestProblem, Language, Problem, Profile, Submission, SubmissionTestCase
from backend.judge.services.contest_archive import export_contest, verify_archive


class ContestArchiveTests(TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings_override = override_settings(DMOJ_PROBLEM_DATA_ROOT=str(self.root / 'packages'))
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        now = timezone.now()
        self.contest = Contest.objects.create(key='ARCHIVE', name='Archive', start_time=now-timedelta(hours=2), end_time=now-timedelta(hours=1))
        self.problem = Problem.objects.create(code='SUM', name='Sum', description='Original statement')
        ContestProblem.objects.create(contest=self.contest, problem=self.problem)
        user = User.objects.create_user('archivist', email='private@example.com', password='private-secret')
        profile, _ = Profile.objects.get_or_create(user=user)
        language = Language.objects.create(key='ARCHPY', name='Python', short_name='Py', common_name='Python')
        submission = Submission.objects.create(contest=self.contest, problem=self.problem, user=profile, language=language, source='print(42)', status='D', result='AC')
        SubmissionTestCase.objects.create(submission=submission, case=1, status='AC')
        package = self.root / 'packages' / 'SUM' / 'cases'
        package.mkdir(parents=True)
        (package / '1.in').write_bytes(b'encrypted-test-data')
        self.target = self.root / 'archive.zip'

    def test_export_preserves_snapshot_packages_and_results_without_credentials(self):
        export_contest(self.contest.key, self.target)
        self.problem.description = 'Changed'
        self.problem.save()
        manifest = verify_archive(self.target)
        self.assertEqual(manifest['missing_packages'], [])
        with ZipFile(self.target) as archive:
            raw = archive.read('data.json').decode()
            data = json.loads(raw)
            self.assertEqual(data['problems'][0]['fields']['description'], 'Original statement')
            self.assertEqual(data['submissions'][0]['fields']['source'], 'print(42)')
            self.assertEqual(data['test_results'][0]['fields']['status'], 'AC')
            self.assertNotIn('private@example.com', raw)
            self.assertNotIn('password', raw)
            self.assertEqual(archive.read('problems/SUM/cases/1.in'), b'encrypted-test-data')

    def test_running_contest_is_rejected(self):
        self.contest.end_time = timezone.now() + timedelta(hours=1)
        self.contest.save()
        with self.assertRaises(ValueError):
            export_contest(self.contest.key, self.target)
        self.assertFalse(self.target.exists())

    def test_existing_backup_is_never_overwritten(self):
        self.target.write_bytes(b'existing')
        with self.assertRaises(FileExistsError):
            export_contest(self.contest.key, self.target)
        self.assertEqual(self.target.read_bytes(), b'existing')

    def test_tampering_is_detected(self):
        export_contest(self.contest.key, self.target)
        altered = self.root / 'altered.zip'
        with ZipFile(self.target) as original, ZipFile(altered, 'w') as output:
            for name in original.namelist():
                output.writestr(name, b'changed' if name == 'data.json' else original.read(name))
        with self.assertRaises(ValueError):
            verify_archive(altered)

    def test_missing_package_is_reported(self):
        (self.root / 'packages' / 'SUM' / 'cases' / '1.in').unlink()
        (self.root / 'packages' / 'SUM' / 'cases').rmdir()
        (self.root / 'packages' / 'SUM').rmdir()
        self.assertEqual(export_contest(self.contest.key, self.target)['missing_packages'], ['SUM'])

    def test_download_requires_staff_and_returns_verified_zip(self):
        from rest_framework.test import APIClient
        from io import BytesIO
        api = APIClient()
        url = f'/api/v2/admin/contest/{self.contest.key}/archive'
        self.assertIn(api.post(url).status_code, (401, 403))
        user = User.objects.get(username='archivist')
        api.force_authenticate(user=user)
        self.assertEqual(api.post(url).status_code, 403)
        user.is_staff = True
        user.save()
        response = api.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', response['Cache-Control'])
        try:
            raw = b''.join(response.streaming_content)
            self.assertEqual(verify_archive(BytesIO(raw))['contest_key'], self.contest.key)
        finally:
            response.close()

    def test_download_rejects_running_contest_and_missing_package(self):
        from rest_framework.test import APIClient
        api = APIClient()
        user = User.objects.get(username='archivist')
        user.is_staff = True
        user.save()
        api.force_authenticate(user=user)
        url = f'/api/v2/admin/contest/{self.contest.key}/archive'
        self.contest.end_time = timezone.now() + timedelta(hours=1)
        self.contest.save()
        self.assertEqual(api.post(url).status_code, 400)
        self.contest.end_time = timezone.now() - timedelta(hours=1)
        self.contest.save()
        with override_settings(DMOJ_PROBLEM_DATA_ROOT=str(self.root / 'missing')):
            self.assertEqual(api.post(url).status_code, 409)
