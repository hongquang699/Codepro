from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from backend.judge.models import Contest, ContestParticipation, Language, Problem, Profile, Submission
from backend.contest_admin.models.models import ContestAdminRole
from .models import AntiCheatAppeal, AntiCheatCase, AntiCheatPenalty, ScanJob, SimilarityResult
from .services.scanner import process_scan


SOURCE = '''#include <bits/stdc++.h>
using namespace std;
int main() {
    int a, b, c;
    cin >> a >> b >> c;
    int answer = a + b - c;
    if (answer > 0) {
        cout << answer << endl;
    } else {
        cout << 0 << endl;
    }
    return 0;
}
'''


class AntiCheatFlowTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.contest = Contest.objects.create(
            key='AC_TEST', name='Anti-cheat test', start_time=now,
            end_time=now + timedelta(hours=2),
        )
        self.problem = Problem.objects.create(code='AC_TEST_P', name='Test problem', description='Test')
        self.language = Language.objects.create(
            key='CPP17_AC', name='C++17', short_name='C++17', common_name='C++',
        )
        self.admin = User.objects.create_user('ac_admin', password='test', is_staff=True)
        self.other_admin = User.objects.create_user('ac_admin_2', password='test', is_staff=True)
        self.alice = User.objects.create_user('ac_alice', password='test')
        self.bob = User.objects.create_user('ac_bob', password='test')
        for user in (self.alice, self.bob):
            profile, _ = Profile.objects.get_or_create(user=user)
            ContestParticipation.objects.create(contest=self.contest, user=profile)
        self.client = APIClient()
        with self.captureOnCommitCallbacks(execute=True):
            self.a = Submission.objects.create(
                contest=self.contest, problem=self.problem, language=self.language,
                user=self.alice.profile, source=SOURCE,
            )
            self.b = Submission.objects.create(
                contest=self.contest, problem=self.problem, language=self.language,
                user=self.bob.profile, source=SOURCE.replace('answer', 'result'),
            )

    def _admin_url(self, path):
        return f'/api/v1/admin/contests/{self.contest.key}/anti-cheat/{path}'

    def test_submission_event_queues_scan_and_match_needs_review(self):
        self.assertEqual(ScanJob.objects.filter(contest=self.contest, status='PENDING').count(), 2)
        job = ScanJob.objects.create(contest=self.contest, status='RUNNING')
        process_scan(job.pk)
        self.assertEqual(SimilarityResult.objects.filter(contest=self.contest).count(), 1)
        case = AntiCheatCase.objects.get(contest=self.contest)
        self.assertEqual(case.status, 'OPEN')
        self.assertFalse(ContestParticipation.objects.get(contest=self.contest, user=self.alice.profile).is_disqualified)
        self.assertFalse(AntiCheatPenalty.objects.exists())

    def test_evidence_is_private_and_appeal_cannot_erase_other_disqualification(self):
        job = ScanJob.objects.create(contest=self.contest, status='RUNNING')
        process_scan(job.pk)
        case = AntiCheatCase.objects.get(contest=self.contest)
        evidence = self._admin_url(f'cases/{case.pk}/evidence')
        self.client.force_authenticate(user=self.alice)
        self.assertEqual(self.client.get(evidence).status_code, 403)
        self.client.force_authenticate(user=self.admin)
        self.assertEqual(self.client.get(evidence).status_code, 200)
        response = self.client.post(self._admin_url(f'cases/{case.pk}/confirm'),
                                    {'reason': 'Manual review found matching structure.'}, format='json')
        self.assertEqual(response.status_code, 200)
        response = self.client.post(self._admin_url(f'cases/{case.pk}/penalties'), {
            'kind': 'DISQUALIFY', 'user_id': self.alice.pk,
            'reason': 'Manual review confirmed shared source.'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ContestParticipation.objects.get(contest=self.contest, user=self.alice.profile).is_disqualified)
        penalty = AntiCheatPenalty.objects.get(pk=response.data['id'])
        self.client.force_authenticate(user=self.bob)
        self.assertEqual(self.client.get('/api/v1/anti-cheat/penalties').data['penalties'], [])
        self.client.force_authenticate(user=self.alice)
        response = self.client.post('/api/v1/anti-cheat/appeals', {
            'penalty_id': penalty.pk, 'reason': 'Please review the source comparison.'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        appeal = AntiCheatAppeal.objects.get(pk=response.data['id'])
        self.assertEqual(self.client.post('/api/v1/anti-cheat/appeals', {
            'penalty_id': penalty.pk, 'reason': 'Please review this decision again.'
        }, format='json').status_code, 400)
        self.client.force_authenticate(user=self.admin)
        self.assertEqual(self.client.post(self._admin_url(f'appeals/{appeal.pk}/resolve'), {
            'decision': 'UPHELD', 'explanation': 'Independent review found insufficient evidence.'
        }, format='json').status_code, 403)
        self.client.force_authenticate(user=self.other_admin)
        response = self.client.post(self._admin_url(f'appeals/{appeal.pk}/resolve'), {
            'decision': 'UPHELD', 'explanation': 'Independent review found insufficient evidence.'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['manual_reinstatement_required'])
        penalty.refresh_from_db()
        self.assertIsNotNone(penalty.revoked_at)
        self.assertTrue(ContestParticipation.objects.get(contest=self.contest, user=self.alice.profile).is_disqualified)

    def test_security_boundaries_and_csrf(self):
        job = ScanJob.objects.create(contest=self.contest, status='RUNNING')
        process_scan(job.pk)
        case = AntiCheatCase.objects.get(contest=self.contest)
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self._admin_url('dashboard')).status_code, 401)
        self.client.force_authenticate(user=self.alice)
        self.assertEqual(self.client.get(self._admin_url('dashboard')).status_code, 403)
        self.assertEqual(self.client.get(self._admin_url(f'cases/{case.pk}/evidence')).status_code, 403)
        self.assertEqual(self.client.post(self._admin_url('scans'), {}, format='json').status_code, 403)

        reviewer = User.objects.create_user('ac_reviewer', password='test')
        ContestAdminRole.objects.create(contest=self.contest, user=reviewer, role='jury_manager')
        self.client.force_authenticate(user=reviewer)
        self.assertEqual(self.client.get(self._admin_url(f'cases/{case.pk}/evidence')).status_code, 200)
        self.assertEqual(self.client.post(self._admin_url(f'cases/{case.pk}/penalties'), {
            'kind': 'DISQUALIFY', 'user_id': self.alice.pk,
            'reason': 'Insufficient authorization must be rejected.'
        }, format='json').status_code, 403)
        self.assertFalse(AntiCheatPenalty.objects.exists())

        other = Contest.objects.create(
            key='AC_OTHER', name='Other contest', start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=2),
        )
        self.client.force_authenticate(user=self.admin)
        self.assertEqual(self.client.get(f'/api/v1/admin/contests/{other.key}/anti-cheat/cases/{case.pk}/evidence').status_code, 404)
        self.assertEqual(self.client.get(f'/api/v1/admin/contests/{other.key}/anti-cheat/scans/{job.pk}').status_code, 404)
        self.assertEqual(self.client.post(self._admin_url('penalties'), {}, format='json').status_code, 400)

        csrf_client = APIClient(enforce_csrf_checks=True)
        csrf_client.force_login(self.admin)
        self.assertEqual(csrf_client.post(self._admin_url('scans'), {}, format='json').status_code, 403)

    def test_audit_failure_rolls_back_case_decision(self):
        job = ScanJob.objects.create(contest=self.contest, status='RUNNING')
        process_scan(job.pk)
        case = AntiCheatCase.objects.get(contest=self.contest)
        self.client.force_authenticate(user=self.admin)
        with patch('backend.anti_cheat.api.views.ContestAuditLog.objects.create', side_effect=DatabaseError('audit unavailable')):
            with self.assertRaises(DatabaseError):
                self.client.post(self._admin_url(f'cases/{case.pk}/confirm'), {
                    'reason': 'Manual review found matching structure.'
                }, format='json')
        case.refresh_from_db()
        self.assertEqual(case.status, 'OPEN')
