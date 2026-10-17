import hashlib

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.contest_admin.models.models import ContestAuditLog
from backend.contest_admin.permissions.permissions import has_contest_permission
from backend.judge.models import Contest, ContestParticipation
from backend.judge.permissions.authentication import BearerTokenAuthentication, JudgeCookieAuthentication
from backend.anti_cheat.models import (
    AntiCheatAppeal, AntiCheatCase, AntiCheatPenalty, AntiCheatSettings, ScanJob, SimilarityResult,
)
from backend.anti_cheat.services.scanner import enqueue_scan


class AuthenticatedAPIView(APIView):
    authentication_classes = [TokenAuthentication, BearerTokenAuthentication, JudgeCookieAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


class ContestAPIView(AuthenticatedAPIView):
    def contest(self, request, contest_id, permission='anti_cheat.view'):
        contest = get_object_or_404(Contest, **({'pk': int(contest_id)} if str(contest_id).isdigit() else {'key': contest_id}))
        if not has_contest_permission(request.user, contest, permission):
            raise PermissionDenied('Không có quyền truy cập dữ liệu chống gian lận của kỳ thi này.')
        return contest

    @staticmethod
    def audit(request, contest, action, target_type='', target_id='', details=''):
        # Administrative actions must not commit without their audit record.
        return ContestAuditLog.objects.create(
            contest=contest, actor=request.user, action=action,
            target_type=target_type, target_id=str(target_id), details=details,
            ip_address=request.META.get('REMOTE_ADDR') or '127.0.0.1',
        )


def _case_payload(case):
    result = case.result
    return {
        'id': case.pk, 'status': case.status, 'reason': case.reason,
        'score': result.score, 'algorithm_version': result.algorithm_version,
        'problem': result.problem.code,
        'submission_a': result.submission_a_id, 'submission_b': result.submission_b_id,
        'user_a_id': result.submission_a.user.user_id,
        'user_b_id': result.submission_b.user.user_id,
        'user_a': result.submission_a.user.user.username,
        'user_b': result.submission_b.user.user.username,
        'language': result.submission_a.language.name,
        'created_at': case.created_at.isoformat(),
        'reviewed_at': case.reviewed_at.isoformat() if case.reviewed_at else None,
    }


def _case_queryset(contest):
    return AntiCheatCase.objects.filter(contest=contest).select_related(
        'result__problem', 'result__submission_a__user__user',
        'result__submission_b__user__user', 'result__submission_a__language'
    )


class DashboardView(ContestAPIView):
    def get(self, request, contest_id):
        contest = self.contest(request, contest_id)
        jobs = ScanJob.objects.filter(contest=contest)
        cases = AntiCheatCase.objects.filter(contest=contest)
        config, _ = AntiCheatSettings.objects.get_or_create(contest=contest)
        completed = jobs.filter(status='COMPLETED')
        full_scan_count = completed.filter(target_submission__isnull=True).order_by('-finished_at').values_list('processed', flat=True).first() or 0
        targeted_count = completed.filter(target_submission__isnull=False).values('target_submission_id').distinct().count()
        flagged_ids = set()
        for first_id, second_id in SimilarityResult.objects.filter(contest=contest).values_list('submission_a_id', 'submission_b_id'):
            flagged_ids.update((first_id, second_id))
        return Response({'contest': contest.key, 'enabled': config.enabled,
                         'threshold': config.similarity_threshold,
                         'scan_mode': config.scan_mode,
                         'scanned_submissions': max(full_scan_count, targeted_count),
                         'flagged_submissions': len(flagged_ids),
                         'high_risk_cases': cases.filter(result__score__gte=95, status__in=['OPEN', 'UNDER_REVIEW']).count(),
                         'scans': jobs.count(), 'pending_scans': jobs.filter(status__in=['PENDING', 'RUNNING']).count(),
                         'cases': cases.count(), 'open_cases': cases.filter(status__in=['OPEN', 'UNDER_REVIEW']).count(),
                         'confirmed_cases': cases.filter(status='CONFIRMED').count(),
                         'latest_scan': _job_payload(jobs.first()) if jobs.exists() else None})


def _job_payload(job):
    return {'id': job.pk, 'status': job.status, 'processed': job.processed,
            'total': job.total, 'matches': job.matches, 'error': job.error,
            'target_submission': job.target_submission_id,
            'created_at': job.created_at.isoformat(),
            'finished_at': job.finished_at.isoformat() if job.finished_at else None}


class SettingsView(ContestAPIView):
    def get(self, request, contest_id):
        contest = self.contest(request, contest_id)
        config, _ = AntiCheatSettings.objects.get_or_create(contest=contest)
        return Response({'enabled': config.enabled, 'similarity_threshold': config.similarity_threshold,
                         'scan_mode': config.scan_mode, 'min_tokens': config.min_tokens})

    @transaction.atomic
    def patch(self, request, contest_id):
        contest = self.contest(request, contest_id, 'anti_cheat.manage')
        config, _ = AntiCheatSettings.objects.get_or_create(contest=contest)
        before = {'enabled': config.enabled, 'similarity_threshold': config.similarity_threshold,
                  'scan_mode': config.scan_mode, 'min_tokens': config.min_tokens}
        values = request.data
        if 'enabled' in values:
            if not isinstance(values['enabled'], bool):
                raise ValidationError({'enabled': 'Cần giá trị true hoặc false.'})
            config.enabled = values['enabled']
        if 'similarity_threshold' in values:
            value = values['similarity_threshold']
            if type(value) is not int or not 50 <= value <= 100:
                raise ValidationError({'similarity_threshold': 'Ngưỡng phải từ 50 đến 100.'})
            config.similarity_threshold = value
        if 'min_tokens' in values:
            value = values['min_tokens']
            if type(value) is not int or not 20 <= value <= 500:
                raise ValidationError({'min_tokens': 'Số token tối thiểu phải từ 20 đến 500.'})
            config.min_tokens = value
        if 'scan_mode' in values:
            if values['scan_mode'] not in ('realtime', 'scheduled', 'manual'):
                raise ValidationError({'scan_mode': 'Chế độ quét không hợp lệ.'})
            config.scan_mode = values['scan_mode']
        config.save()
        self.audit(request, contest, 'ANTI_CHEAT_SETTINGS', 'settings', config.pk,
                   f'before={before}; after={{"enabled": {config.enabled}, "threshold": {config.similarity_threshold}, "scan_mode": "{config.scan_mode}", "min_tokens": {config.min_tokens}}}')
        return self.get(request, contest_id)


class ScansView(ContestAPIView):
    def get(self, request, contest_id):
        contest = self.contest(request, contest_id)
        return Response({'scans': [_job_payload(job) for job in ScanJob.objects.filter(contest=contest)[:50]]})

    @transaction.atomic
    def post(self, request, contest_id):
        contest = self.contest(request, contest_id, 'anti_cheat.manage')
        config, _ = AntiCheatSettings.objects.get_or_create(contest=contest)
        if not config.enabled:
            raise ValidationError({'enabled': 'Hãy bật quét chống gian lận trước.'})
        job, created = enqueue_scan(contest, request.user)
        if created:
            self.audit(request, contest, 'ANTI_CHEAT_SCAN_QUEUED', 'scan', job.pk)
        return Response(_job_payload(job), status=202)


class ScanDetailView(ContestAPIView):
    def get(self, request, contest_id, scan_id):
        contest = self.contest(request, contest_id)
        return Response(_job_payload(get_object_or_404(ScanJob, pk=scan_id, contest=contest)))


class RetryScanView(ContestAPIView):
    @transaction.atomic
    def post(self, request, contest_id, scan_id):
        contest = self.contest(request, contest_id, 'anti_cheat.manage')
        job = get_object_or_404(ScanJob, pk=scan_id, contest=contest)
        if job.status != 'FAILED':
            raise ValidationError({'status': 'Chỉ được thử lại lượt quét lỗi.'})
        job.status, job.error, job.processed, job.matches = 'PENDING', '', 0, 0
        job.started_at = job.finished_at = None
        job.save(update_fields=['status', 'error', 'processed', 'matches', 'started_at', 'finished_at'])
        self.audit(request, contest, 'ANTI_CHEAT_SCAN_RETRY', 'scan', job.pk)
        return Response(_job_payload(job), status=202)


class SimilaritiesView(ContestAPIView):
    def get(self, request, contest_id):
        contest = self.contest(request, contest_id)
        results = SimilarityResult.objects.filter(contest=contest).select_related(
            'problem', 'submission_a__user__user', 'submission_b__user__user'
        ).order_by('-score', '-created_at')[:100]
        return Response({'similarities': [{
            'id': result.pk, 'case_id': getattr(getattr(result, 'case', None), 'pk', None),
            'problem': result.problem.code, 'score': result.score,
            'submission_a': result.submission_a_id, 'submission_b': result.submission_b_id,
            'user_a': result.submission_a.user.user.username,
            'user_b': result.submission_b.user.user.username,
            'algorithm_version': result.algorithm_version,
        } for result in results]})


class GroupsView(ContestAPIView):
    def get(self, request, contest_id):
        contest = self.contest(request, contest_id)
        graph = {}

        def find(value):
            graph.setdefault(value, value)
            if graph[value] != value:
                graph[value] = find(graph[value])
            return graph[value]

        for result in SimilarityResult.objects.filter(contest=contest).select_related('submission_a__user__user', 'submission_b__user__user'):
            a = result.submission_a.user.user.username
            b = result.submission_b.user.user.username
            graph[find(a)] = find(b)
        groups = {}
        for username in graph:
            groups.setdefault(find(username), []).append(username)
        return Response({'groups': [sorted(users) for users in groups.values() if len(users) >= 3]})


class CasesView(ContestAPIView):
    def get(self, request, contest_id):
        contest = self.contest(request, contest_id)
        cases = _case_queryset(contest)
        status = request.query_params.get('status')
        if status:
            cases = cases.filter(status=status.upper())
        return Response({'cases': [_case_payload(case) for case in cases[:100]]})


class CaseDetailView(ContestAPIView):
    def get(self, request, contest_id, case_id):
        contest = self.contest(request, contest_id, 'anti_cheat.review')
        case = get_object_or_404(_case_queryset(contest), pk=case_id)
        return Response({'case': _case_payload(case)})


class EvidenceView(ContestAPIView):
    def get(self, request, contest_id, case_id):
        contest = self.contest(request, contest_id, 'anti_cheat.review')
        case = get_object_or_404(_case_queryset(contest), pk=case_id)
        result = case.result
        a, b = result.submission_a, result.submission_b
        return Response({'case': _case_payload(case), 'evidence': result.evidence,
                         'source_a': a.source, 'source_b': b.source,
                         'source_a_sha256': result.source_a_sha256,
                         'source_b_sha256': result.source_b_sha256,
                         'source_unchanged': (
                             hashlib.sha256(a.source.encode()).hexdigest() == result.source_a_sha256
                             and hashlib.sha256(b.source.encode()).hexdigest() == result.source_b_sha256
                         )})


class CaseDecisionView(ContestAPIView):
    action = None

    def post(self, request, contest_id, case_id):
        contest = self.contest(request, contest_id, 'anti_cheat.review')
        reason = request.data.get('reason')
        if not isinstance(reason, str) or not 10 <= len(reason.strip()) <= 4000:
            raise ValidationError({'reason': 'Cần lý do từ 10 đến 4000 ký tự.'})
        with transaction.atomic():
            case = get_object_or_404(AntiCheatCase.objects.select_for_update(), pk=case_id, contest=contest)
            if case.status not in ('OPEN', 'UNDER_REVIEW'):
                raise ValidationError({'status': 'Hồ sơ này đã có quyết định.'})
            case.status = 'CONFIRMED' if self.action == 'confirm' else 'DISMISSED'
            case.reason = reason.strip()
            case.reviewer = request.user
            case.reviewed_at = timezone.now()
            case.save(update_fields=['status', 'reason', 'reviewer', 'reviewed_at'])
            self.audit(request, contest, f'ANTI_CHEAT_{case.status}', 'case', case.pk, case.reason)
        return Response({'id': case.pk, 'status': case.status})


class PenaltiesView(ContestAPIView):
    def get(self, request, contest_id):
        contest = self.contest(request, contest_id, 'anti_cheat.review')
        penalties = AntiCheatPenalty.objects.filter(case__contest=contest).select_related(
            'case', 'user', 'issued_by'
        ).order_by('-created_at')[:100]
        return Response({'penalties': [{
            'id': item.pk, 'case_id': item.case_id, 'user': item.user.username,
            'kind': item.kind, 'reason': item.reason,
            'issued_by': item.issued_by.username if item.issued_by else 'system',
            'created_at': item.created_at.isoformat(), 'revoked': bool(item.revoked_at),
        } for item in penalties]})

    def post(self, request, contest_id, case_id=None):
        if case_id is None:
            raise ValidationError({'case_id': 'Cần chọn hồ sơ đã xác nhận.'})
        contest = self.contest(request, contest_id, 'anti_cheat.penalize')
        kind, user_id, reason = request.data.get('kind'), request.data.get('user_id'), request.data.get('reason')
        if kind not in ('WARNING', 'DISQUALIFY') or not isinstance(reason, str) or not 10 <= len(reason.strip()) <= 4000:
            raise ValidationError({'error': 'Loại xử lý hoặc lý do không hợp lệ.'})
        case = get_object_or_404(_case_queryset(contest), pk=case_id)
        if case.status != 'CONFIRMED':
            raise ValidationError({'status': 'Phải xác nhận hồ sơ trước khi xử lý.'})
        allowed_ids = (case.result.submission_a.user.user_id, case.result.submission_b.user.user_id)
        if type(user_id) is not int or user_id not in allowed_ids:
            raise ValidationError({'user_id': 'Người bị xử lý phải thuộc hồ sơ này.'})
        with transaction.atomic():
            penalty, created = AntiCheatPenalty.objects.get_or_create(
                case=case, user_id=user_id, kind=kind,
                defaults={'reason': reason.strip(), 'issued_by': request.user},
            )
            if not created:
                raise ValidationError({'error': 'Quyết định này đã tồn tại.'})
            if kind == 'DISQUALIFY':
                ContestParticipation.objects.filter(contest=contest, user__user_id=user_id).update(is_disqualified=True)
            self.audit(request, contest, 'ANTI_CHEAT_PENALTY', 'penalty', penalty.pk,
                       f'{kind} user={user_id}; reason={reason.strip()}')
        return Response({'id': penalty.pk, 'kind': kind, 'user_id': user_id}, status=201)


class AppealsView(ContestAPIView):
    def get(self, request, contest_id):
        contest = self.contest(request, contest_id, 'anti_cheat.review')
        appeals = AntiCheatAppeal.objects.filter(penalty__case__contest=contest).select_related('appellant', 'penalty')[:100]
        return Response({'appeals': [{
            'id': item.pk, 'case_id': item.penalty.case_id, 'penalty_id': item.penalty_id,
            'appellant': item.appellant.username, 'reason': item.reason,
            'status': item.status, 'decision': item.decision,
        } for item in appeals]})


class ResolveAppealView(ContestAPIView):
    def post(self, request, contest_id, appeal_id):
        contest = self.contest(request, contest_id, 'anti_cheat.appeal')
        decision, explanation = request.data.get('decision'), request.data.get('explanation')
        if decision not in ('UPHELD', 'REJECTED') or not isinstance(explanation, str) or len(explanation.strip()) < 10:
            raise ValidationError({'error': 'Cần quyết định và giải thích ít nhất 10 ký tự.'})
        with transaction.atomic():
            appeal = get_object_or_404(AntiCheatAppeal.objects.select_for_update().select_related('penalty__case'),
                                       pk=appeal_id, penalty__case__contest=contest)
            if appeal.status != 'OPEN':
                raise ValidationError({'status': 'Khiếu nại đã được xử lý.'})
            if appeal.penalty.issued_by_id == request.user.id:
                raise PermissionDenied('Người ra quyết định không được tự xét khiếu nại của quyết định đó.')
            appeal.status, appeal.decision, appeal.reviewer = decision, explanation.strip(), request.user
            appeal.resolved_at = timezone.now()
            appeal.save(update_fields=['status', 'decision', 'reviewer', 'resolved_at'])
            if decision == 'UPHELD':
                penalty = appeal.penalty
                penalty.revoked_at = timezone.now()
                penalty.save(update_fields=['revoked_at'])
                # ContestParticipation has no record of which subsystem disqualified
                # a user. Clearing this flag could undo an unrelated admin decision.
                # Reinstatement therefore needs an explicit contest admin action.
                appeal.penalty.case.status = 'CLOSED'
                appeal.penalty.case.save(update_fields=['status'])
            else:
                appeal.penalty.case.status = 'CLOSED'
                appeal.penalty.case.save(update_fields=['status'])
            self.audit(request, contest, 'ANTI_CHEAT_APPEAL_RESOLVED', 'appeal', appeal.pk,
                       f'{decision}: {explanation.strip()}')
        return Response({'id': appeal.pk, 'status': appeal.status,
                         'manual_reinstatement_required': decision == 'UPHELD' and appeal.penalty.kind == 'DISQUALIFY'})


class AuditView(ContestAPIView):
    def get(self, request, contest_id):
        contest = self.contest(request, contest_id, 'anti_cheat.review')
        logs = ContestAuditLog.objects.filter(contest=contest, action__startswith='ANTI_CHEAT_').select_related('actor')[:100]
        return Response({'audit': [{
            'id': item.pk, 'action': item.action, 'actor': item.actor.username if item.actor else 'system',
            'target_type': item.target_type, 'target_id': item.target_id,
            'details': item.details, 'created_at': item.created_at.isoformat(),
        } for item in logs]})


class MyPenaltiesView(AuthenticatedAPIView):
    def get(self, request):
        penalties = AntiCheatPenalty.objects.filter(user=request.user).select_related('case__contest').order_by('-created_at')[:100]
        return Response({'penalties': [{
            'id': item.pk, 'contest': item.case.contest.key, 'kind': item.kind,
            'reason': item.reason, 'created_at': item.created_at.isoformat(),
            'revoked': bool(item.revoked_at),
        } for item in penalties]})


class MyAppealsView(AuthenticatedAPIView):
    def get(self, request):
        appeals = AntiCheatAppeal.objects.filter(appellant=request.user).select_related('penalty__case__contest').order_by('-created_at')[:100]
        return Response({'appeals': [{
            'id': item.pk, 'penalty_id': item.penalty_id,
            'contest': item.penalty.case.contest.key,
            'status': item.status, 'reason': item.reason, 'decision': item.decision,
            'created_at': item.created_at.isoformat(),
        } for item in appeals]})

    @transaction.atomic
    def post(self, request):
        penalty_id, reason = request.data.get('penalty_id'), request.data.get('reason')
        if type(penalty_id) is not int or not isinstance(reason, str) or not 10 <= len(reason.strip()) <= 4000:
            raise ValidationError({'error': 'Cần mã quyết định và lý do từ 10 đến 4000 ký tự.'})
        penalty = get_object_or_404(
            AntiCheatPenalty.objects.select_for_update().select_related('case__contest'),
            pk=penalty_id, user=request.user, revoked_at__isnull=True,
        )
        if AntiCheatAppeal.objects.filter(penalty=penalty).exists():
            raise ValidationError({'error': 'Quyết định này đã có khiếu nại.'})
        appeal = AntiCheatAppeal.objects.create(penalty=penalty, appellant=request.user, reason=reason.strip())
        AntiCheatCase.objects.filter(pk=penalty.case_id).update(status='APPEALED')
        ContestAuditLog.objects.create(
            contest=penalty.case.contest, actor=request.user,
            action='ANTI_CHEAT_APPEAL_CREATED', target_type='appeal', target_id=str(appeal.pk),
            ip_address=request.META.get('REMOTE_ADDR') or '127.0.0.1',
        )
        return Response({'id': appeal.pk, 'status': appeal.status}, status=201)
