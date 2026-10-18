import io
import json
import zipfile
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from backend.judge.models import Language, Problem, Profile, Submission
from backend.judge import problem_package

from .models import ProblemVersion, SubmissionVersion
from .service import publish, validate_package


def package(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return output.getvalue()


def valid_files():
    return {
        'manifest.json': json.dumps({'groups': [{'name': 'main', 'points': 100,
            'cases': [{'name': '01'}]}]}),
        'statement.md': '# Sum',
        'cases/01.in': '1 2\n',
        'cases/01.out': '3\n',
    }


class PackageValidationTests(SimpleTestCase):
    def test_valid_package(self):
        statement, groups = validate_package(package(valid_files()))
        self.assertEqual(statement, '# Sum')
        self.assertEqual(groups[0]['cases'][0]['name'], '01')

    def test_rejects_zip_slip(self):
        files = valid_files()
        files['../escape'] = 'bad'
        with self.assertRaises(ValueError):
            validate_package(package(files))

    def test_rejects_unreferenced_private_file(self):
        files = valid_files()
        files['cases/secret.in'] = 'bad'
        with self.assertRaises(ValueError):
            validate_package(package(files))

    def test_rejects_duplicate_group(self):
        files = valid_files()
        manifest = json.loads(files['manifest.json'])
        manifest['groups'].append(manifest['groups'][0])
        files['manifest.json'] = json.dumps(manifest)
        with self.assertRaises(ValueError):
            validate_package(package(files))

    def test_rejects_bomb_ratio(self):
        files = valid_files()
        files['cases/01.in'] = 'a' * 100000
        with self.assertRaises(ValueError):
            validate_package(package(files))


class StorageAccessTests(TestCase):
    def setUp(self):
        self.problem = Problem.objects.create(code='STORAGE1', name='Storage', description='')
        self.user = User.objects.create_user('reader', password='test')
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.path = '/api/v1/problem-storage/problems/STORAGE1/versions'

    def test_reader_cannot_list_or_create(self):
        self.assertEqual(self.client.get(self.path).status_code, 403)
        self.assertEqual(self.client.post(self.path).status_code, 403)

    def test_editor_can_initiate_upload(self):
        group = Group.objects.create(name='problem_editor')
        self.user.groups.add(group)
        with patch('backend.problem_storage.service.s3') as storage:
            storage.return_value.generate_presigned_post.return_value = {
                'url': 'https://minio.example/upload', 'fields': {'key': 'staging/test'}}
            response = self.client.post(self.path)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['method'], 'POST')
        self.assertEqual(self.problem.storage_versions.count(), 1)

    def test_internal_validation_needs_token(self):
        self.assertEqual(self.client.post('/api/v1/problem-storage/internal/validate',
            {'version_id': '00000000-0000-0000-0000-000000000000'}).status_code, 403)

    def test_submission_keeps_published_version(self):
        version = ProblemVersion.objects.create(problem=self.problem, number=1,
            state=ProblemVersion.State.READY, private_key='private/v1.zip',
            statement='# Version one', created_by=self.user)
        publish(version)
        self.problem.refresh_from_db()
        self.assertEqual(self.problem.description, '# Version one')
        self.assertEqual(problem_package.get_statement(self.problem.code)['markdown'], '# Version one')
        language = Language.objects.create(key='PY3', name='Python 3', short_name='Python', common_name='Python')
        profile = Profile.objects.create(user=self.user)
        submission = Submission.objects.create(problem=self.problem, user=profile,
            language=language, source='print(3)')
        self.assertEqual(SubmissionVersion.objects.get(submission=submission).version, version)
