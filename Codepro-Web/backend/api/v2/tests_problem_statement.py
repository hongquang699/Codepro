"""Problem details prefer the Markdown package when a database copy is damaged."""

import tempfile
from pathlib import Path

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from backend.judge.models import Problem


class ProblemStatementSourceTests(TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        settings_override = override_settings(DMOJ_PROBLEM_DATA_ROOT=str(self.root))
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        self.problem = Problem.objects.create(
            code='SOURCE_TEST', name='Source test', description='Công thức $ và $ bị lỗi', is_public=True
        )
        self.api = APIClient()

    def test_package_markdown_takes_precedence(self):
        statement_dir = self.root / self.problem.code / 'statement'
        statement_dir.mkdir(parents=True)
        source = 'Cho hai số $A$ và $B$. Tính $A+B$.'
        (statement_dir / 'statement.md').write_text(source, encoding='utf-8')

        response = self.api.get(f'/api/v2/problem/{self.problem.code}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['object']['description'], source)

    def test_database_description_remains_fallback_without_package(self):
        response = self.api.get(f'/api/v2/problem/{self.problem.code}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['object']['description'], self.problem.description)

    def test_authoring_api_saves_markdown_for_problem_detail(self):
        staff = User.objects.create_user('statement_admin', is_staff=True)
        self.api.force_authenticate(user=staff)
        source = '# Đề mới\nTính $A+B$.'

        saved = self.api.put(
            f'/api/v1/problems/{self.problem.code}/statement',
            {'markdown': source, 'html': source}, format='json'
        )
        detail = self.api.get(f'/api/v2/problem/{self.problem.code}')

        self.assertEqual(saved.status_code, 200)
        self.assertEqual(detail.data['data']['object']['description'], source)
        self.assertEqual(
            (self.root / self.problem.code / 'statement' / 'statement.md').read_text(encoding='utf-8'),
            source
        )
