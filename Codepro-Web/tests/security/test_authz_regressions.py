"""Regression tests for the authorization holes fixed in the 2026-11 security pass."""

import tempfile
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from backend.contest_admin.models.models import ContestAdminRole
from backend.judge.models import Contest, ContestParticipation, ContestProblem, Organization, Problem, Profile
from backend.organizations.models import OrganizationMember, OrganizationPermission, OrganizationRole


def make_user(username, **flags):
    user = User.objects.create_user(username, f'{username}@example.com', 'password123', **flags)
    Profile.objects.get_or_create(user=user)
    return user


def client_for(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@override_settings(DMOJ_PROBLEM_DATA_ROOT=tempfile.gettempdir(), CODEPRO_CONTEST_PACKAGE_ROOT=tempfile.gettempdir())
class ContestAdminScopeTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.teacher = make_user('teacher1')
        self.contest = Contest.objects.create(key='MINE', name='Mine', start_time=now, end_time=now + timedelta(hours=1))
        ContestAdminRole.objects.create(contest=self.contest, user=self.teacher, role='owner')
        self.hidden = Problem.objects.create(code='HIDDEN', name='Hidden', description='secret', is_public=False)
        self.api = client_for(self.teacher)

    def test_cannot_touch_problem_outside_contest(self):
        base = '/api/v1/contest-admin/contests/MINE/problems/HIDDEN'
        self.assertEqual(self.api.get(f'{base}/statement').status_code, 404)
        self.assertEqual(self.api.put(f'{base}/statement', {'statement': 'pwned'}, format='json').status_code, 404)
        self.hidden.refresh_from_db()
        self.assertEqual(self.hidden.description, 'secret')

    def test_cannot_attach_hidden_problem(self):
        response = self.api.post('/api/v1/contest-admin/contests/MINE/problems', {'code': 'HIDDEN'}, format='json')
        self.assertEqual(response.status_code, 404)
        self.assertFalse(ContestProblem.objects.filter(contest=self.contest, problem=self.hidden).exists())

    def test_cannot_edit_shared_public_problem(self):
        public = Problem.objects.create(code='PUB', name='Public', description='orig', is_public=True)
        ContestProblem.objects.create(contest=self.contest, problem=public, order=1, output_prefix='A')
        response = self.api.put('/api/v1/contest-admin/contests/MINE/problems/PUB/statement',
                                {'statement': 'changed'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_rejects_path_like_contest_key(self):
        self.teacher.profile.role = 'teacher'
        self.teacher.profile.save()
        response = self.api.post('/api/v1/contest-admin/contests', {'key': '../../escape', 'name': 'x'}, format='json')
        self.assertEqual(response.status_code, 400)


class OrganizationLinkTests(TestCase):
    def setUp(self):
        self.owner = make_user('orgowner')
        self.org = Organization.objects.create(name='Org', slug='org', short_name='O', owner_id=self.owner.id)
        now = timezone.now()
        self.victim_contest = Contest.objects.create(key='VICTIM', name='Victim', start_time=now,
                                                     end_time=now + timedelta(hours=1))

    def test_cannot_link_foreign_contest(self):
        response = client_for(self.owner).post('/api/v1/organizations/org/contests/',
                                               {'contest_key': 'VICTIM'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_admin_role_cannot_promote_to_owner(self):
        admin_role = OrganizationRole.objects.create(organization=self.org, name='Administrator')
        OrganizationPermission.objects.create(role=admin_role, permission='member.manage')
        owner_role = OrganizationRole.objects.create(organization=self.org, name='Owner')
        OrganizationPermission.objects.create(role=owner_role, permission='*')
        admin = make_user('orgadmin')
        OrganizationMember.objects.create(organization=self.org, user=admin, role=admin_role)
        response = client_for(admin).patch('/api/v1/organizations/org/members/orgadmin/', {'role': 'Owner'},
                                           format='json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(OrganizationMember.objects.get(user=admin).role, admin_role)

    def test_invitations_require_permission(self):
        self.assertEqual(client_for(make_user('stranger')).get('/api/v1/organizations/org/admin/invitations/').status_code, 403)


class PrivilegeEscalationTests(TestCase):
    def test_setter_cannot_grant_superuser(self):
        setter = make_user('setter1', is_staff=True)
        response = client_for(setter).post('/api/v2/admin/users/setter1/role', {'role': 'admin'}, format='json')
        self.assertEqual(response.status_code, 403)
        setter.refresh_from_db()
        self.assertFalse(setter.is_superuser)

    def test_staff_cannot_reset_superuser_password(self):
        make_user('root', is_staff=True, is_superuser=True)
        staff = make_user('staff1', is_staff=True)
        response = client_for(staff).put('/api/v2/user/root', {'password': 'hijacked123'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.get(username='root').check_password('password123'))


class CredentialRevocationTests(TestCase):
    def test_password_change_revokes_drf_token(self):
        user = make_user('alice')
        Token.objects.create(user=user)
        response = self.client.post('/api/v1/auth/login', {'username': 'alice', 'password': 'password123'},
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        session = response.json()['session_token']
        response = self.client.post('/api/v1/auth/change-password', {
            'current_password': 'password123', 'new_password': 'N3w-Passw0rd!x',
            'new_password_confirm': 'N3w-Passw0rd!x'}, content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {session}')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(Token.objects.filter(user=user).exists())

    def test_public_profile_hides_email(self):
        make_user('bob')
        data = self.client.get('/api/v1/users/bob').json()
        self.assertNotIn('bob@example.com', str(data))


class ContestAccessTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.contest = Contest.objects.create(key='CODED', name='Coded', start_time=now + timedelta(hours=1),
                                              end_time=now + timedelta(hours=3), access_code='s3cret', is_visible=True)
        problem = Problem.objects.create(code='SOON', name='Upcoming', is_public=False)
        ContestProblem.objects.create(contest=self.contest, problem=problem, order=1, output_prefix='A')
        self.user = make_user('carol')

    def test_access_code_required(self):
        api = client_for(self.user)
        self.assertEqual(api.post('/api/v1/contests/CODED/register', {}, format='json').status_code, 403)
        self.assertEqual(api.post('/api/v1/contests/CODED/register', {'access_code': 's3cret'},
                                  format='json').status_code, 200)
        self.assertTrue(ContestParticipation.objects.filter(contest=self.contest, user__user=self.user).exists())

    def test_problems_hidden_before_start(self):
        data = client_for(self.user).get('/api/v1/contests/CODED/dashboard').json()
        self.assertNotIn('SOON', str(data))
