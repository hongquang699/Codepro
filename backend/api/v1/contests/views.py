import os
import re
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils import timezone
from rest_framework.authentication import SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication
from django.db.models import Q, Max, Sum

from backend.judge.models import (
    Contest, ContestProblem, ContestParticipation, Problem,
    Submission, Language, Profile, Clarification
)
from backend.judge.bridge import grade_submission
from backend.judge.contest_visibility import contest_visible, visible_contests
from backend.judge.permissions.submissions import can_view_submission_details
from backend.submissions.validators.source import SourceCodeValidator
from backend.submissions.validators.language import LanguageValidator
from backend.judge.permissions.authentication import BearerTokenAuthentication, JudgeCookieAuthentication

def get_current_user(request):
    """Return only the identity verified by DRF authentication."""
    return request.user if request.user.is_authenticated else None


class ContestAPIView(APIView):
    authentication_classes = [TokenAuthentication, BearerTokenAuthentication, JudgeCookieAuthentication, SessionAuthentication]

def check_org_contest_access(contest, user):
    """
    If contest belongs to an organization, user must be an active member of that org (or admin).
    Returns (has_access: bool, error_message: str, org_data: dict or None)
    """
    from backend.organizations.models import OrganizationContest, OrganizationMember
    oc = OrganizationContest.objects.filter(contest=contest).select_related('organization').first()
    if not oc:
        return True, '', None
    org = oc.organization
    org_info = {'slug': org.slug, 'name': org.short_name or org.name}
    if not user:
        return False, f'Cuộc thi này là kỳ thi nội bộ của tổ chức "{org_info["name"]}". Vui lòng đăng nhập và tham gia tổ chức để xem.', org_info
    if user.is_staff or user.is_superuser:
        return True, '', org_info
    if hasattr(org, 'owner_id') and org.owner_id == user.id:
        return True, '', org_info
    is_mem = OrganizationMember.objects.filter(organization=org, user=user, status='active').exists()
    if not is_mem:
        return False, f'Cuộc thi này là kỳ thi nội bộ của tổ chức "{org_info["name"]}". Bạn phải là thành viên của tổ chức để truy cập và tham gia.', org_info
    return True, '', org_info

def get_contest_or_404(contest_id, request):
    """Retrieve contest by ID or Key."""
    if str(contest_id).isdigit():
        c = get_object_or_404(Contest, id=int(contest_id))
    else:
        c = Contest.objects.filter(key__iexact=contest_id).first()
        if not c:
            c = Contest.objects.filter(key__iexact=contest_id.replace('-', '_')).first()
        if not c:
            c = Contest.objects.filter(key__iexact=contest_id.replace('_', '-')).first()
        if not c:
            c = get_object_or_404(Contest, key=contest_id)
    if not contest_visible(c, 'web') and not request.user.is_staff:
        raise Http404('Cuộc thi không hiển thị trên web')
    return c

def get_problem_in_contest(contest, problem_id):
    """Retrieve problem by prefix letter (A, B, C) or problem code."""
    cp = ContestProblem.objects.filter(contest=contest, output_prefix__iexact=problem_id).select_related('problem').first()
    if not cp:
        cp = ContestProblem.objects.filter(contest=contest, problem__code__iexact=problem_id).select_related('problem').first()
    if not cp:
        # Check order if integer
        if str(problem_id).isdigit():
            cp = ContestProblem.objects.filter(contest=contest, order=int(problem_id)).select_related('problem').first()
    return cp

def get_problem_user_status(user, problem, contest=None):
    """Return status: 'solved', 'attempted', or 'not_attempted'"""
    if not user:
        return 'not_attempted'
    qs = Submission.objects.filter(problem=problem, user__user=user)
    if contest:
        qs = qs.filter(contest=contest)
    if not qs.exists():
        return 'not_attempted'
    if qs.filter(result='AC').exists():
        return 'solved'
    return 'attempted'


# ── CONTEST LIST & LANDING ──────────────────────────────────────────────────
class ContestListAPIView(ContestAPIView):
    def get(self, request):
        contests = Contest.objects.filter(visible_contests('web')).order_by('-start_time')
        now = timezone.now()

        user = get_current_user(request)
        user_reg_contest_ids = set()
        active_contest_key = None
        if user:
            user_reg_contest_ids = set(ContestParticipation.objects.filter(user__user=user).values_list('contest_id', flat=True))
            act_part = ContestParticipation.objects.filter(
                user__user=user,
                contest__end_time__gte=now
            ).select_related('contest').first()
            if act_part:
                active_contest_key = act_part.contest.key

        results = []
        for c in contests:
            if now < c.start_time:
                c_status = 'UPCOMING'
            elif now <= c.end_time:
                c_status = 'RUNNING'
            else:
                c_status = 'FINISHED'

            results.append({
                'id': c.id,
                'key': c.key,
                'name': c.name,
                'description': c.description,
                'start_time': c.start_time.isoformat(),
                'end_time': c.end_time.isoformat(),
                'time_limit': c.time_limit,
                'duration_minutes': int(c.time_limit / 60) if c.time_limit else 180,
                'status': c_status,
                'is_rated': c.is_rated,
                'format': c.format_name,
                'problems_count': c.contest_problems.count(),
                'participants_count': c.participants.count(),
                'is_registered': c.id in user_reg_contest_ids,
                'is_other_active': bool(active_contest_key and active_contest_key != c.key)
            })
        return Response({'status': 200, 'data': results, 'active_contest_key': active_contest_key})


class ContestDetailAPIView(ContestAPIView):
    def get(self, request, contest_id):
        c = get_contest_or_404(contest_id, request)
        now = timezone.now()
        if now < c.start_time:
            c_status = 'UPCOMING'
        elif now <= c.end_time:
            c_status = 'RUNNING'
        else:
            c_status = 'FINISHED'

        user = get_current_user(request)
        is_registered = False
        active_other_contest = None
        if user:
            is_registered = ContestParticipation.objects.filter(contest=c, user__user=user).exists()
            act_part = ContestParticipation.objects.filter(
                user__user=user,
                contest__end_time__gte=now
            ).exclude(contest=c).select_related('contest').first()
            if act_part:
                active_other_contest = {
                    'key': act_part.contest.key,
                    'name': act_part.contest.name
                }

        has_access, err_msg, org_data = check_org_contest_access(c, user)

        total_secs = max(0, int((c.end_time - c.start_time).total_seconds()))
        remaining_secs = max(0, int((c.end_time - now).total_seconds())) if c_status == 'RUNNING' else 0

        return Response({
            'status': 200,
            'data': {
                'id': c.id,
                'key': c.key,
                'name': c.name,
                'description': c.description,
                'start_time': c.start_time.isoformat(),
                'end_time': c.end_time.isoformat(),
                'status': c_status,
                'is_rated': c.is_rated,
                'format': c.format_name,
                'is_registered': is_registered,
                'active_other_contest': active_other_contest,
                'duration_seconds': total_secs,
                'remaining_seconds': remaining_secs,
                'problems_count': c.contest_problems.count(),
                'participants_count': c.participants.count(),
                'is_org_contest': bool(org_data),
                'organization': org_data,
                'has_org_access': has_access,
                'org_access_error': err_msg if not has_access else ''
            }
        })


class ContestRegisterAPIView(ContestAPIView):
    def post(self, request, contest_id):
        c = get_contest_or_404(contest_id, request)
        user = get_current_user(request)
        if not user:
            return Response({'status': 401, 'error': {'message': 'Vui lòng đăng nhập để tham gia cuộc thi.'}}, status=401)
        if not c.is_visible or c.end_time < timezone.now():
            return Response({'status': 403, 'error': {'message': 'Kỳ thi không mở đăng ký.'}}, status=403)

        has_access, err_msg, org_data = check_org_contest_access(c, user)
        if not has_access:
            return Response({
                'status': 403,
                'error': {'message': err_msg},
                'requires_org_membership': True,
                'organization': org_data
            }, status=403)

        prof, _ = Profile.objects.get_or_create(user=user)

        now = timezone.now()
        # Chặn nếu thí sinh đang tham gia một cuộc thi khác chưa kết thúc
        active_part = ContestParticipation.objects.filter(
            user=prof,
            contest__end_time__gte=now
        ).exclude(contest=c).select_related('contest').first()

        if active_part:
            other_c = active_part.contest
            return Response({
                'status': 400,
                'error': {
                    'code': 'ALREADY_IN_ANOTHER_CONTEST',
                    'message': f'Bạn đang tham gia cuộc thi "{other_c.name}". Mỗi thí sinh chỉ được tham gia 1 cuộc thi tại một thời điểm. Vui lòng rời cuộc thi đó trước!',
                    'active_contest_key': other_c.key,
                    'active_contest_name': other_c.name
                }
            }, status=400)

        part, created = ContestParticipation.objects.get_or_create(
            contest=c,
            user=prof,
            defaults={'real_start': now}
        )
        return Response({
            'status': 200,
            'data': {
                'message': 'Đã tham gia cuộc thi thành công!',
                'contest_key': c.key,
                'contest_name': c.name,
                'is_registered': True,
                'registered_at': part.real_start.isoformat() if part.real_start else now.isoformat()
            }
        })

    def delete(self, request, contest_id):
        return ContestLeaveAPIView().post(request, contest_id)


class ContestLeaveAPIView(ContestAPIView):
    def post(self, request, contest_id):
        c = get_contest_or_404(contest_id, request)
        user = get_current_user(request)
        if not user:
            return Response({'status': 401, 'error': {'message': 'Vui lòng đăng nhập để rời cuộc thi.'}}, status=401)

        prof = Profile.objects.filter(user=user).first()
        if prof:
            ContestParticipation.objects.filter(contest=c, user=prof).delete()

        return Response({
            'status': 200,
            'data': {
                'message': f'Đã rời khỏi cuộc thi "{c.name}" thành công!',
                'contest_key': c.key,
                'contest_name': c.name,
                'is_registered': False,
                'left': True
            }
        })

    def delete(self, request, contest_id):
        return self.post(request, contest_id)


# ── CONTEST DASHBOARD ────────────────────────────────────────────────────────
class ContestDashboardAPIView(ContestAPIView):
    def get(self, request, contest_id):
        c = get_contest_or_404(contest_id, request)
        user = get_current_user(request)
        now = timezone.now()

        is_registered = False
        active_other_contest = None
        if user:
            is_registered = ContestParticipation.objects.filter(contest=c, user__user=user).exists()
            act_part = ContestParticipation.objects.filter(
                user__user=user,
                contest__end_time__gte=now
            ).exclude(contest=c).select_related('contest').first()
            if act_part:
                active_other_contest = {
                    'key': act_part.contest.key,
                    'name': act_part.contest.name
                }

        if now < c.start_time:
            c_status = 'UPCOMING'
        elif now <= c.end_time:
            c_status = 'RUNNING'
        else:
            c_status = 'FINISHED'

        # Build problems list with user status
        cps = ContestProblem.objects.filter(contest=c).select_related('problem').order_by('order')
        problems_list = []
        user_solved = 0
        user_total_score = 0.0

        for cp in cps:
            status_val = get_problem_user_status(user, cp.problem, contest=c)
            if status_val == 'solved':
                user_solved += 1
                user_total_score += cp.points

            # Count overall solves
            solved_count = Submission.objects.filter(contest=c, problem=cp.problem, result='AC').values('user').distinct().count()
            total_subs = Submission.objects.filter(contest=c, problem=cp.problem).count()

            problems_list.append({
                'letter': cp.output_prefix or chr(64 + cp.order),
                'order': cp.order,
                'code': cp.problem.code,
                'name': cp.problem.name,
                'points': cp.points,
                'status': status_val,
                'solved_count': solved_count,
                'submission_count': total_subs
            })

        total_secs = max(0, int((c.end_time - c.start_time).total_seconds()))
        elapsed_secs = max(0, int((now - c.start_time).total_seconds())) if now >= c.start_time else 0
        remaining_secs = max(0, int((c.end_time - now).total_seconds())) if c_status == 'RUNNING' else 0
        progress_pct = min(100, int((elapsed_secs / total_secs) * 100)) if total_secs > 0 and now >= c.start_time else 0

        return Response({
            'status': 200,
            'data': {
                'contest': {
                    'id': c.id,
                    'key': c.key,
                    'name': c.name,
                    'description': c.description,
                    'start_time': c.start_time.isoformat(),
                    'end_time': c.end_time.isoformat(),
                    'status': c_status,
                    'progress_pct': progress_pct,
                    'remaining_seconds': remaining_secs,
                    'format': c.format_name,
                    'is_rated': c.is_rated,
                    'is_registered': is_registered
                },
                'problems': problems_list,
                'user_stats': {
                    'username': user.username if user else None,
                    'is_registered': is_registered,
                    'solved_count': user_solved,
                    'total_problems': len(problems_list),
                    'total_score': user_total_score
                },
                'is_registered': is_registered,
                'active_other_contest': active_other_contest
            }
        })


# ── CONTEST PROBLEMS ────────────────────────────────────────────────────────
class ContestProblemsListAPIView(ContestAPIView):
    def get(self, request, contest_id):
        c = get_contest_or_404(contest_id, request)
        user = get_current_user(request)
        if not user or not c.is_visible or timezone.now() < c.start_time:
            return Response({'status': 403, 'error': {'message': 'Bài thi chưa được mở.'}}, status=403)
        has_access, err_msg, org_data = check_org_contest_access(c, user)
        if not has_access:
            return Response({
                'status': 403,
                'error': {'message': err_msg},
                'requires_org_membership': True,
                'organization': org_data
            }, status=403)
        cps = ContestProblem.objects.filter(contest=c).select_related('problem').order_by('order')

        res = []
        for cp in cps:
            status_val = get_problem_user_status(user, cp.problem, contest=c)
            res.append({
                'letter': cp.output_prefix or chr(64 + cp.order),
                'order': cp.order,
                'code': cp.problem.code,
                'name': cp.problem.name,
                'points': cp.points,
                'time_limit': cp.problem.time_limit,
                'memory_limit': cp.problem.memory_limit,
                'status': status_val
            })
        return Response({'status': 200, 'data': res})


class ContestProblemDetailAPIView(ContestAPIView):
    def get(self, request, contest_id, problem_id):
        c = get_contest_or_404(contest_id, request)
        user = get_current_user(request)
        if not user or not c.is_visible or timezone.now() < c.start_time:
            return Response({'status': 403, 'error': {'message': 'Bài thi chưa được mở.'}}, status=403)
        has_access, err_msg, _ = check_org_contest_access(c, user)
        if not has_access:
            return Response({'status': 403, 'error': {'message': err_msg}}, status=403)
        cp = get_problem_in_contest(c, problem_id)
        if not cp:
            return Response({'status': 404, 'error': {'message': f'Bài tập {problem_id} không tồn tại trong cuộc thi.'}}, status=404)

        prob = cp.problem
        user_status = get_problem_user_status(user, prob, contest=c)

        # Build sidebar problem list
        all_cps = ContestProblem.objects.filter(contest=c).select_related('problem').order_by('order')
        sidebar = []
        for item in all_cps:
            s_val = get_problem_user_status(user, item.problem, contest=c)
            sidebar.append({
                'letter': item.output_prefix or chr(64 + item.order),
                'code': item.problem.code,
                'name': item.problem.name,
                'points': item.points,
                'status': s_val,
                'is_current': item.id == cp.id
            })

        return Response({
            'status': 200,
            'data': {
                'contest': {
                    'key': c.key,
                    'name': c.name,
                    'end_time': c.end_time.isoformat()
                },
                'problem': {
                    'letter': cp.output_prefix or chr(64 + cp.order),
                    'code': prob.code,
                    'name': prob.name,
                    'points': cp.points,
                    'time_limit': prob.time_limit,
                    'memory_limit': prob.memory_limit,
                    'description': prob.description,
                    'user_status': user_status
                },
                'sidebar': sidebar
            }
        })


# ── CONTEST SUBMIT & SUBMISSIONS ─────────────────────────────────────────────
class ContestProblemSubmitAPIView(ContestAPIView):
    def post(self, request, contest_id, problem_id):
        c = get_contest_or_404(contest_id, request)
        user = get_current_user(request)
        if not user or not user.is_active:
            return Response({'status': 401, 'error': {'message': 'Vui lòng đăng nhập để nộp bài.'}}, status=401)

        now = timezone.now()
        if not c.is_visible or not (c.start_time <= now <= c.end_time):
            return Response({'status': 403, 'error': {'message': 'Kỳ thi chưa mở hoặc đã kết thúc.'}}, status=403)
        has_access, err_msg, _ = check_org_contest_access(c, user)
        if not has_access:
            return Response({'status': 403, 'error': {'message': err_msg}}, status=403)

        cp = get_problem_in_contest(c, problem_id)
        if not cp:
            return Response({'status': 404, 'error': {'message': f'Bài tập {problem_id} không thuộc cuộc thi.'}}, status=404)

        prob = cp.problem
        lang_key = request.data.get('language', 'CPP17')
        source_code = request.data.get('source_code') or request.data.get('source') or ''

        valid_source, source_error = SourceCodeValidator.validate(source_code)
        if not valid_source:
            return Response({'status': 400, 'error': {'message': source_error}}, status=400)

        valid_lang, lang_error, lang = LanguageValidator.validate(lang_key)
        if not valid_lang:
            return Response({'status': 400, 'error': {'message': lang_error}}, status=400)

        prof, _ = Profile.objects.get_or_create(user=user)

        if not ContestParticipation.objects.filter(contest=c, user=prof, is_disqualified=False).exists():
            return Response({'status': 403, 'error': {'message': 'Bạn chưa đăng ký hoặc đã bị loại khỏi kỳ thi này.'}},
                            status=403)

        sub = Submission.objects.create(
            problem=prob,
            user=prof,
            language=lang,
            source=source_code,
            contest=c,
            status='QU',
            result=None,
            points=0.0
        )

        # Grade immediately via judge bridge
        try:
            grade_submission(sub.id)
            sub.refresh_from_db()
        except Exception:
            sub.status = 'D'
            sub.result = 'SE'
            sub.points = 0.0
            sub.error = 'Judge unavailable; submission requires rejudge.'
            sub.save(update_fields=['status', 'result', 'points', 'error'])

        return Response({
            'status': 201,
            'data': {
                'submission_id': sub.id,
                'problem_letter': cp.output_prefix or chr(64 + cp.order),
                'problem_code': prob.code,
                'status': sub.status,
                'result': sub.result,
                'score': sub.points or 0.0,
                'message': 'Nộp bài thành công!'
            }
        }, status=201)


class ContestSubmissionsListAPIView(ContestAPIView):
    def get(self, request, contest_id):
        c = get_contest_or_404(contest_id, request)
        qs = Submission.objects.filter(contest=c).select_related('problem', 'user__user', 'language').order_by('-date')

        user_filter = request.GET.get('user') or request.GET.get('username')
        if user_filter:
            qs = qs.filter(user__user__username=user_filter)

        prob_filter = request.GET.get('problem')
        if prob_filter:
            qs = qs.filter(Q(problem__code__iexact=prob_filter))

        # Map problem letter
        cp_map = {}
        for cp in ContestProblem.objects.filter(contest=c):
            cp_map[cp.problem_id] = cp.output_prefix or chr(64 + cp.order)

        res = []
        for s in qs[:50]:
            letter = cp_map.get(s.problem_id, 'A')
            res.append({
                'id': s.id,
                'user': s.user.user.username,
                'problem_letter': letter,
                'problem_code': s.problem.code,
                'problem_name': s.problem.name,
                'language': s.language.name if s.language else 'C++',
                'status': s.status,
                'result': s.result or 'Judging',
                'score': round(s.points or 0, 1),
                'time_ms': int((s.time or 0) * 1000),
                'memory_mb': round((s.memory or 0) / 1024, 1),
                'date': s.date.strftime('%H:%M:%S %d/%m/%Y')
            })

        return Response({'status': 200, 'data': res})


# ── SUBMISSION DETAIL, STATUS & RESULT ───────────────────────────────────────
class SubmissionUnifiedDetailAPIView(ContestAPIView):
    def get(self, request, submission_id):
        sub = get_object_or_404(Submission.objects.select_related('problem', 'user__user', 'language', 'contest'), id=submission_id)
        user = get_current_user(request)

        # Source code visibility check
        can_view = can_view_submission_details(user, sub)

        # Get problem letter in contest if present
        letter = 'A'
        if sub.contest:
            cp = ContestProblem.objects.filter(contest=sub.contest, problem=sub.problem).first()
            if cp:
                letter = cp.output_prefix or chr(64 + cp.order)

        # Testcase details
        cases = []
        for tc in (sub.test_cases.all().order_by('case') if can_view else []):
            cases.append({
                'case': tc.case,
                'status': tc.status,
                'time_ms': int((tc.time or 0) * 1000),
                'memory_mb': round((tc.memory or 0) / 1024, 1),
                'points': tc.points,
                'total_points': tc.total_points,
                'feedback': tc.feedback
            })

        return Response({
            'status': 200,
            'data': {
                'id': sub.id,
                'contest_key': sub.contest.key if sub.contest else None,
                'contest_name': sub.contest.name if sub.contest else None,
                'problem_letter': letter,
                'problem_code': sub.problem.code,
                'problem_name': sub.problem.name,
                'user': sub.user.user.username,
                'language': sub.language.name if sub.language else 'C++',
                'status': sub.status,
                'verdict': sub.result or 'JUDGING',
                'score': round(sub.points or 0, 1),
                'max_score': 100.0,
                'time_ms': int((sub.time or 0) * 1000),
                'memory_mb': round((sub.memory or 0) / 1024, 1),
                'date': sub.date.strftime('%H:%M:%S %d/%m/%Y'),
                'can_view_source': can_view,
                'source_code': sub.source if can_view else '[Mã nguồn được bảo mật theo quy chế cuộc thi]',
                'testcases': cases
            }
        })


class SubmissionStatusPollAPIView(ContestAPIView):
    def get(self, request, submission_id):
        sub = get_object_or_404(Submission, id=submission_id)
        is_done = sub.status == 'D' or bool(sub.result)
        cases_count = sub.test_cases.count()
        progress_text = 'Đang chấm kết quả...' if not is_done else 'Đã hoàn thành'
        if not is_done and cases_count > 0:
            progress_text = f'Đang chạy Test #{cases_count + 1}'

        return Response({
            'status': 200,
            'data': {
                'id': sub.id,
                'status': sub.status,
                'verdict': sub.result or 'JUDGING',
                'is_done': is_done,
                'score': round(sub.points or 0, 1),
                'time_ms': int((sub.time or 0) * 1000),
                'memory_mb': round((sub.memory or 0) / 1024, 1),
                'progress': progress_text
            }
        })


# ── CONTEST REALTIME SCOREBOARD / RANKING ────────────────────────────────────
class ContestRankingAPIView(ContestAPIView):
    def get(self, request, contest_id):
        c = get_contest_or_404(contest_id, request)
        cps = ContestProblem.objects.filter(contest=c).select_related('problem').order_by('order')
        problems_meta = [
            {'letter': cp.output_prefix or chr(64 + cp.order), 'code': cp.problem.code, 'points': cp.points}
            for cp in cps
        ]

        participants = ContestParticipation.objects.filter(contest=c).select_related('user__user')
        scoreboard = []

        for part in participants:
            u = part.user.user
            p_scores = {}
            total_solved = 0
            total_pts = 0.0
            total_penalty = 0

            for cp in cps:
                letter = cp.output_prefix or chr(64 + cp.order)
                subs = Submission.objects.filter(contest=c, problem=cp.problem, user=part.user).order_by('date')
                if not subs.exists():
                    p_scores[letter] = {'status': 'none', 'score': 0, 'tries': 0, 'time': 0}
                    continue

                ac_sub = subs.filter(result='AC').first()
                if ac_sub:
                    tries = subs.filter(date__lte=ac_sub.date).count()
                    secs = max(0, int((ac_sub.date - c.start_time).total_seconds()))
                    p_scores[letter] = {
                        'status': 'AC',
                        'score': cp.points,
                        'tries': tries,
                        'time': int(secs / 60)
                    }
                    total_solved += 1
                    total_pts += cp.points
                    total_penalty += int(secs / 60) + (tries - 1) * 20
                else:
                    best_sub = subs.order_by('-points').first()
                    p_scores[letter] = {
                        'status': 'WA',
                        'score': best_sub.points or 0.0,
                        'tries': subs.count(),
                        'time': 0
                    }
                    total_pts += (best_sub.points or 0.0)

            scoreboard.append({
                'user': u.username,
                'name': u.get_full_name() or u.username,
                'rating': part.user.rating or 1500,
                'rank_title': part.user.display_rank,
                'solved': total_solved,
                'total_score': total_pts,
                'penalty': total_penalty,
                'problems': p_scores
            })

        # Sort scoreboard by score desc, penalty asc
        scoreboard.sort(key=lambda x: (-x['total_score'], x['penalty']))
        for i, row in enumerate(scoreboard):
            row['rank'] = i + 1

        return Response({
            'status': 200,
            'data': {
                'contest': {
                    'key': c.key,
                    'name': c.name,
                    'problems': problems_meta
                },
                'scoreboard': scoreboard
            }
        })


# ── ANNOUNCEMENTS & CLARIFICATIONS ──────────────────────────────────────────
class ContestAnnouncementsAPIView(ContestAPIView):
    def get(self, request, contest_id):
        c = get_contest_or_404(contest_id, request)
        # Standard contest notices
        notices = [
            {
                'id': 1,
                'title': f'Chào mừng các thí sinh tham gia {c.name}',
                'content': 'Kỳ thi đã chính thức bắt đầu. Chúc các thí sinh bình tĩnh, tự tin và đạt kết quả cao nhất!',
                'time': c.start_time.strftime('%H:%M %d/%m/%Y'),
                'is_urgent': True
            },
            {
                'id': 2,
                'title': 'Quy định chấm bài và phòng thi',
                'content': 'Hệ thống áp dụng sandbox tự động. Mã nguồn không được sử dụng các hàm can thiệp hệ điều hành trái phép.',
                'time': c.start_time.strftime('%H:%M %d/%m/%Y'),
                'is_urgent': False
            }
        ]
        return Response({'status': 200, 'data': notices})


class ContestClarificationsAPIView(ContestAPIView):
    def get(self, request, contest_id):
        c = get_contest_or_404(contest_id, request)
        clars = Clarification.objects.filter(is_public=True).select_related('asked_by__user', 'problem').order_by('-asked_at')
        res = []
        for cl in clars:
            res.append({
                'id': cl.id,
                'problem_code': cl.problem.code if cl.problem else 'Chung',
                'question': cl.question,
                'answer': cl.answer or 'Chưa có câu trả lời từ ban ra đề.',
                'asked_by': cl.asked_by.user.username if cl.asked_by else 'Thí sinh',
                'asked_at': cl.asked_at.strftime('%H:%M %d/%m')
            })
        return Response({'status': 200, 'data': res})

    def post(self, request, contest_id):
        c = get_contest_or_404(contest_id, request)
        user = get_current_user(request)
        if not user:
            return Response({'status': 401, 'error': {'message': 'Vui lòng đăng nhập để gửi thắc mắc.'}}, status=401)

        question = request.data.get('question', '').strip()
        prob_code = request.data.get('problem_code', '').strip()

        if not question:
            return Response({'status': 400, 'error': {'message': 'Nội dung thắc mắc không được trống.'}}, status=400)

        prob = Problem.objects.filter(code__iexact=prob_code).first() if prob_code else None
        prof, _ = Profile.objects.get_or_create(user=user)

        clar = Clarification.objects.create(
            problem=prob,
            asked_by=prof,
            question=question,
            is_public=True,
            answer='Ban giám khảo đã nhận câu hỏi và sẽ phản hồi sớm nhất.'
        )
        return Response({'status': 201, 'data': {'message': 'Đã gửi thắc mắc thành công!', 'id': clar.id}}, status=201)
