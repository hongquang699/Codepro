import os
import json
import csv
import io
import re
import time
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q, Count
from django.conf import settings
from django.http import HttpResponse
from security.encryption import file_cipher

from backend.judge.models import (
    Contest, ContestProblem, ContestParticipation, Problem,
    Submission, SubmissionTestCase, Language, Profile, Clarification
)
from backend.judge.bridge import grade_submission, _judge_server_online, JUDGE_SERVER_URL
from backend.judge.contest_visibility import valid_display_target
from backend.judge.permissions.authentication import BearerTokenAuthentication, JudgeCookieAuthentication
from ..models.models import ContestAuditLog, ContestAdminRole, ContestAnnouncement, ContestBan
from ..permissions.permissions import resolve_admin_user, has_contest_permission, get_user_contest_role
from ..services.audit_service import log_contest_audit
from ..services.rejudge_service import rejudge_contest_submission, rejudge_contest_problem, rejudge_entire_contest
from ..services.package_service import get_problem_storage_dir, sync_problem_to_contest_storage


def get_contest(contest_id):
    if str(contest_id).isdigit():
        return get_object_or_404(Contest, id=int(contest_id))
    return get_object_or_404(Contest, key=contest_id)


class ContestAdminAPIView(APIView):
    authentication_classes = [TokenAuthentication, BearerTokenAuthentication, JudgeCookieAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]


# ── 1. CONTESTS PORTAL LIST ──────────────────────────────────────────────────
class ContestAdminListView(ContestAdminAPIView):
    def get(self, request):
        user = resolve_admin_user(request)
        if not user:
            return Response({'status': 401, 'error': 'Vui lòng đăng nhập.'}, status=401)

        contests = Contest.objects.all()
        if not (user.is_staff or user.is_superuser):
            from backend.organizations.models import OrganizationContest
            assigned = ContestAdminRole.objects.filter(user=user).values('contest_id')
            owned = OrganizationContest.objects.filter(organization__owner_id=user.id).values('contest_id')
            contests = contests.filter(Q(id__in=assigned) | Q(id__in=owned))
        contests = contests.order_by('-start_time')
        now = timezone.now()
        data = []
        for c in contests:
            if now < c.start_time:
                c_status = 'UPCOMING'
            elif now <= c.end_time:
                c_status = 'RUNNING'
            else:
                c_status = 'FINISHED'

            data.append({
                'id': c.id,
                'key': c.key,
                'name': c.name,
                'format': c.format_name,
                'status': c_status,
                'start_time': c.start_time.isoformat(),
                'end_time': c.end_time.isoformat(),
                'is_rated': c.is_rated,
                'is_visible': c.is_visible,
                'display_target': c.display_target,
                'hide_scoreboard': c.hide_scoreboard,
                'problems_count': c.contest_problems.count(),
                'participants_count': c.participants.count(),
                'submissions_count': Submission.objects.filter(contest=c).count()
            })
        return Response({'status': 200, 'data': data})

    def post(self, request):
        user = resolve_admin_user(request)
        if not user or not user.is_active or not (user.is_staff or user.is_superuser or getattr(user.profile, 'role', '') == 'teacher'):
            return Response({'status': 403, 'error': 'Không có quyền tạo kỳ thi mới.'}, status=403)

        d = request.data
        key = d.get('key', '').strip()
        name = d.get('name', '').strip()
        if not key or not name:
            return Response({'status': 400, 'error': 'Mã và tên kỳ thi không được để trống.'}, status=400)

        if Contest.objects.filter(key=key).exists():
            return Response({'status': 400, 'error': f'Kỳ thi mã {key} đã tồn tại.'}, status=400)
        display_target = d.get('display_target', 'both')
        if not valid_display_target(display_target):
            return Response({'status': 400, 'error': 'Nơi hiển thị không hợp lệ.'}, status=400)

        start = d.get('start_time') or timezone.now()
        duration = int(d.get('time_limit', 10800))
        end = d.get('end_time') or (timezone.now() + timezone.timedelta(seconds=duration))

        c = Contest.objects.create(
            key=key,
            name=name,
            description=d.get('description', ''),
            format_name=d.get('format', 'icpc'),
            start_time=start,
            end_time=end,
            time_limit=duration,
            is_rated=bool(d.get('is_rated', True)),
            is_visible=bool(d.get('is_visible', True)),
            display_target=display_target
        )
        ContestAdminRole.objects.create(contest=c, user=user, role='owner')
        log_contest_audit(c, user, 'CREATE_CONTEST', details=f"Tạo kỳ thi mới {c.key} - {c.name}")
        return Response({'status': 201, 'message': 'Tạo kỳ thi thành công!', 'data': {'key': c.key, 'name': c.name}}, status=201)


# ── 2. DASHBOARD ─────────────────────────────────────────────────────────────
class ContestAdminDashboardView(ContestAdminAPIView):
    def get(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'contest.view'):
            return Response({'status': 403, 'error': 'Không có quyền truy cập quản trị kỳ thi này.'}, status=403)

        now = timezone.now()
        if now < c.start_time:
            c_status = 'UPCOMING'
            time_remaining = int((c.start_time - now).total_seconds())
        elif now <= c.end_time:
            c_status = 'RUNNING'
            time_remaining = int((c.end_time - now).total_seconds())
        else:
            c_status = 'FINISHED'
            time_remaining = 0

        subs = Submission.objects.filter(contest=c)
        total_subs = subs.count()
        ac_subs = subs.filter(result='AC').count()
        ac_rate = round((ac_subs / total_subs * 100) if total_subs > 0 else 0.0, 1)

        # Judge Queue
        queue_count = Submission.objects.filter(status__in=['QU', 'P', 'G', 'queued', 'grading', 'pending']).count()
        judge_online = _judge_server_online()

        user_role = get_user_contest_role(user, c)

        return Response({
            'status': 200,
            'data': {
                'contest': {
                    'id': c.id,
                    'key': c.key,
                    'name': c.name,
                    'description': c.description,
                    'format': c.format_name,
                    'status': c_status,
                    'start_time': c.start_time.isoformat(),
                    'end_time': c.end_time.isoformat(),
                    'time_remaining_seconds': time_remaining,
                    'is_rated': c.is_rated,
                    'is_visible': c.is_visible,
                    'hide_scoreboard': c.hide_scoreboard,
                    'scoreboard_freeze': c.scoreboard_freeze.isoformat() if c.scoreboard_freeze else None,
                    'access_code': c.access_code
                },
                'stats': {
                    'participants_count': c.participants.count(),
                    'problems_count': c.contest_problems.count(),
                    'submissions_count': total_subs,
                    'ac_count': ac_subs,
                    'ac_rate': ac_rate,
                    'pending_clarifications': Clarification.objects.filter(contest=c, answer='').count(),
                    'announcements_count': c.contest_announcements.count(),
                    'judge_queue': queue_count,
                    'judge_workers_online': 8 if judge_online else 0,
                    'judge_status': 'ONLINE' if judge_online else 'OFFLINE',
                    'errors_count': subs.filter(result__in=['CE', 'IE', 'TLE']).count()
                },
                'user_role': user_role
            }
        })


# ── 3. SETTINGS & SCOREBOARD FREEZE ──────────────────────────────────────────
class ContestAdminSettingsView(ContestAdminAPIView):
    def get(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'contest.view'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        return Response({
            'status': 200,
            'data': {
                'id': c.id,
                'key': c.key,
                'name': c.name,
                'description': c.description,
                'format': c.format_name,
                'start_time': c.start_time.isoformat(),
                'end_time': c.end_time.isoformat(),
                'time_limit': c.time_limit,
                'is_rated': c.is_rated,
                'rate_all': c.rate_all,
                'is_visible': c.is_visible,
                'display_target': c.display_target,
                'hide_scoreboard': c.hide_scoreboard,
                'scoreboard_freeze': c.scoreboard_freeze.isoformat() if c.scoreboard_freeze else '',
                'access_code': c.access_code
            }
        })

    def put(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'contest.edit'):
            return Response({'status': 403, 'error': 'Không có quyền thay đổi cài đặt kỳ thi.'}, status=403)

        d = request.data
        if 'name' in d: c.name = d['name'].strip()
        if 'description' in d: c.description = d['description'].strip()
        if 'format' in d: c.format_name = d['format']
        if 'time_limit' in d: c.time_limit = int(d['time_limit'])
        if 'is_rated' in d: c.is_rated = bool(d['is_rated'])
        if 'rate_all' in d: c.rate_all = bool(d['rate_all'])
        if 'is_visible' in d: c.is_visible = bool(d['is_visible'])
        if 'display_target' in d:
            if not valid_display_target(d['display_target']):
                return Response({'status': 400, 'error': 'Nơi hiển thị không hợp lệ.'}, status=400)
            c.display_target = d['display_target']
        if 'hide_scoreboard' in d: c.hide_scoreboard = bool(d['hide_scoreboard'])
        if 'access_code' in d: c.access_code = d['access_code'].strip()

        if 'start_time' in d and d['start_time']:
            c.start_time = d['start_time']
        if 'end_time' in d and d['end_time']:
            c.end_time = d['end_time']
        if 'scoreboard_freeze' in d:
            c.scoreboard_freeze = d['scoreboard_freeze'] if d['scoreboard_freeze'] else None

        c.save()
        log_contest_audit(c, user, 'UPDATE_SETTINGS', details="Cập nhật cấu hình kỳ thi")
        return Response({'status': 200, 'message': 'Cập nhật cấu hình kỳ thi thành công!'})


class ContestAdminFreezeScoreboardView(ContestAdminAPIView):
    def post(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'ranking.manage'):
            return Response({'status': 403, 'error': 'Không có quyền thao tác đóng băng bảng điểm.'}, status=403)

        action = request.data.get('action') # 'freeze' or 'unfreeze'
        if action == 'freeze':
            c.hide_scoreboard = True
            if not c.scoreboard_freeze:
                c.scoreboard_freeze = timezone.now()
            msg = 'Đã đóng băng bảng điểm (Scoreboard Frozen)'
        else:
            c.hide_scoreboard = False
            c.scoreboard_freeze = None
            msg = 'Đã mở khóa bảng điểm công khai (Scoreboard Unfrozen)'
        c.save()
        log_contest_audit(c, user, 'FREEZE_SCOREBOARD', details=msg)
        return Response({'status': 200, 'message': msg, 'hide_scoreboard': c.hide_scoreboard})


# ── 4. PROBLEMS MANAGEMENT ───────────────────────────────────────────────────
class ContestAdminProblemsView(ContestAdminAPIView):
    def get(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'problem.view'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        cps = ContestProblem.objects.filter(contest=c).select_related('problem').order_by('order', 'output_prefix')
        data = []
        for cp in cps:
            p = cp.problem
            subs = Submission.objects.filter(contest=c, problem=p)
            sub_count = subs.count()
            ac_count = subs.filter(result='AC').values('user').distinct().count()
            data.append({
                'id': cp.id,
                'problem_id': p.id,
                'prefix': cp.output_prefix or 'A',
                'order': cp.order,
                'code': p.code,
                'name': p.name,
                'points': cp.points,
                'time_limit': p.time_limit,
                'memory_limit': p.memory_limit,
                'difficulty': p.difficulty,
                'status': 'Ready' if p.status == 'published' else 'Draft',
                'solved_count': ac_count,
                'submissions_count': sub_count,
                'is_internal': p.is_organization_private
            })
        return Response({'status': 200, 'data': data})

    def post(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'problem.create'):
            return Response({'status': 403, 'error': 'Không có quyền thêm bài tập vào kỳ thi.'}, status=403)

        d = request.data
        code = d.get('code', '').strip().upper()
        prefix = d.get('prefix', '').strip().upper()
        points = float(d.get('points', 100.0))
        is_new = bool(d.get('is_new', False))

        if not prefix:
            existing_count = c.contest_problems.count()
            prefix = chr(ord('A') + existing_count)

        if is_new:
            name = d.get('name', '').strip()
            if not code or not name:
                return Response({'status': 400, 'error': 'Mã và tên bài tập không được để trống.'}, status=400)
            if Problem.objects.filter(code=code).exists():
                return Response({'status': 400, 'error': f'Mã bài tập {code} đã tồn tại.'}, status=400)

            prob = Problem.objects.create(
                code=code,
                name=name,
                description=d.get('description', f'Đề bài {name} trong kỳ thi {c.name}.'),
                time_limit=float(d.get('time_limit', 1.0)),
                memory_limit=int(d.get('memory_limit', 262144)),
                points=points,
                difficulty=d.get('difficulty', 'medium'),
                is_public=False,
                is_organization_private=True,
                status='published'
            )
            # Create cases dir
            os.makedirs(os.path.join(settings.DMOJ_PROBLEM_DATA_ROOT, code, 'cases'), exist_ok=True)
        else:
            prob = Problem.objects.filter(code=code).first()
            if not prob:
                return Response({'status': 404, 'error': f'Không tìm thấy bài tập có mã "{code}".'}, status=404)

        order = c.contest_problems.count() + 1
        cp, created = ContestProblem.objects.get_or_create(
            contest=c, problem=prob,
            defaults={'output_prefix': prefix, 'points': points, 'order': order}
        )
        if not created:
            cp.output_prefix = prefix
            cp.points = points
            cp.save()

        # Sync package storage
        try:
            sync_problem_to_contest_storage(c, cp)
        except Exception:
            pass

        log_contest_audit(c, user, 'ADD_PROBLEM', 'problem', prob.code, f"Gán bài {prefix} - {prob.code} ({points}đ)")
        return Response({'status': 201, 'message': f'Đã thêm bài tập {prefix} ({prob.code}) vào kỳ thi!'}, status=201)

    def delete(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'problem.create'):
            return Response({'status': 403, 'error': 'Không có quyền gỡ bài tập.'}, status=403)

        code = request.data.get('code') or request.GET.get('code')
        cp = ContestProblem.objects.filter(contest=c, problem__code=code).first()
        if not cp:
            return Response({'status': 404, 'error': 'Không tìm thấy bài tập trong kỳ thi.'}, status=404)

        prob_code = cp.problem.code
        cp.delete()
        log_contest_audit(c, user, 'REMOVE_PROBLEM', 'problem', prob_code, f"Gỡ bài {prob_code} khỏi kỳ thi")
        return Response({'status': 200, 'message': f'Đã gỡ bài tập {prob_code} khỏi kỳ thi.'})


class ContestAdminProblemStatementView(ContestAdminAPIView):
    def get(self, request, contest_id, problem_code):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'problem.view'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        prob = get_object_or_404(Problem, code=problem_code)
        return Response({
            'status': 200,
            'data': {
                'code': prob.code,
                'name': prob.name,
                'statement': prob.description or '',
                'time_limit': prob.time_limit,
                'memory_limit': prob.memory_limit
            }
        })

    def put(self, request, contest_id, problem_code):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'problem.edit'):
            return Response({'status': 403, 'error': 'Không có quyền chỉnh sửa đề bài.'}, status=403)

        prob = get_object_or_404(Problem, code=problem_code)
        stmt = request.data.get('statement', '')
        prob.description = stmt
        if 'name' in request.data: prob.name = request.data['name'].strip()
        if 'time_limit' in request.data: prob.time_limit = float(request.data['time_limit'])
        if 'memory_limit' in request.data: prob.memory_limit = int(request.data['memory_limit'])
        prob.save()

        # Update statement in contest storage
        cp = ContestProblem.objects.filter(contest=c, problem=prob).first()
        if cp:
            sync_problem_to_contest_storage(c, cp)

        log_contest_audit(c, user, 'EDIT_STATEMENT', 'problem', prob.code, f"Chỉnh sửa đề bài {prob.code}")
        return Response({'status': 200, 'message': 'Lưu đề bài thành công!'})


class ContestAdminProblemTestcasesView(ContestAdminAPIView):
    def get(self, request, contest_id, problem_code):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'testcase.manage'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        prob = get_object_or_404(Problem, code=problem_code)
        cases_dir = os.path.join(settings.DMOJ_PROBLEM_DATA_ROOT, prob.code, 'cases')
        testcases = []
        if os.path.isdir(cases_dir):
            files = sorted(os.listdir(cases_dir))
            for f in files:
                if f.endswith('.in'):
                    base = f[:-3]
                    out_f = f"{base}.out"
                    in_path = os.path.join(cases_dir, f)
                    out_path = os.path.join(cases_dir, out_f)
                    testcases.append({
                        'id': base,
                        'input_file': f,
                        'output_file': out_f if os.path.exists(out_path) else None,
                        'input_size': len(file_cipher.read_file(in_path)),
                        'output_size': len(file_cipher.read_file(out_path)) if os.path.exists(out_path) else 0,
                        'status': 'Valid' if os.path.exists(out_path) else 'Missing Output'
                    })
        return Response({'status': 200, 'data': testcases, 'count': len(testcases)})

    def post(self, request, contest_id, problem_code):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'testcase.manage'):
            return Response({'status': 403, 'error': 'Không có quyền thêm testcase.'}, status=403)

        prob = get_object_or_404(Problem, code=problem_code)
        cases_dir = os.path.join(settings.DMOJ_PROBLEM_DATA_ROOT, prob.code, 'cases')
        os.makedirs(cases_dir, exist_ok=True)

        existing_count = len([f for f in os.listdir(cases_dir) if f.endswith('.in')])
        test_id = request.data.get('id') or f"{existing_count + 1:02d}"
        if not isinstance(test_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', test_id):
            return Response({'status': 400, 'error': 'Mã testcase không hợp lệ.'}, status=400)
        inp = request.data.get('input', '')
        outp = request.data.get('output', '')

        file_cipher.write_file(os.path.join(cases_dir, f"{test_id}.in"), inp.encode('utf-8'))
        file_cipher.write_file(os.path.join(cases_dir, f"{test_id}.out"), outp.encode('utf-8'))

        # Sync storage
        cp = ContestProblem.objects.filter(contest=c, problem=prob).first()
        if cp:
            sync_problem_to_contest_storage(c, cp)

        log_contest_audit(c, user, 'UPLOAD_TESTCASE', 'testcase', f"{prob.code}/{test_id}", f"Thêm testcase #{test_id}")
        return Response({'status': 201, 'message': f'Thêm testcase #{test_id} thành công!'}, status=201)

    def delete(self, request, contest_id, problem_code):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'testcase.manage'):
            return Response({'status': 403, 'error': 'Không có quyền xóa testcase.'}, status=403)

        prob = get_object_or_404(Problem, code=problem_code)
        test_id = request.data.get('id') or request.GET.get('id')
        if not isinstance(test_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', test_id):
            return Response({'status': 400, 'error': 'Mã testcase không hợp lệ.'}, status=400)
        cases_dir = os.path.join(settings.DMOJ_PROBLEM_DATA_ROOT, prob.code, 'cases')
        in_p = os.path.join(cases_dir, f"{test_id}.in")
        out_p = os.path.join(cases_dir, f"{test_id}.out")
        if os.path.exists(in_p): os.remove(in_p)
        if os.path.exists(out_p): os.remove(out_p)

        log_contest_audit(c, user, 'DELETE_TESTCASE', 'testcase', f"{prob.code}/{test_id}", f"Xóa testcase #{test_id}")
        return Response({'status': 200, 'message': f'Đã xóa testcase #{test_id}.'})


# ── 5. PARTICIPANTS MANAGEMENT ───────────────────────────────────────────────
class ContestAdminParticipantsView(ContestAdminAPIView):
    def get(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'participant.manage'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        parts = ContestParticipation.objects.filter(contest=c).select_related('user', 'user__user').order_by('-score', 'cumulative_time')
        banned_user_ids = set(ContestBan.objects.filter(contest=c).values_list('user_id', flat=True))

        data = []
        for rank, p in enumerate(parts, start=1):
            u = p.user.user
            is_banned = u.id in banned_user_ids or p.is_disqualified
            subs_count = Submission.objects.filter(contest=c, user=p.user).count()
            data.append({
                'id': p.id,
                'user_id': u.id,
                'username': u.username,
                'display_name': u.get_full_name() or u.username,
                'rating': p.user.rating or 1500,
                'rank': rank if not is_banned else '-',
                'score': p.score,
                'penalty': p.cumulative_time,
                'status': 'Banned' if is_banned else 'Active',
                'submissions_count': subs_count,
                'joined_at': p.real_start.isoformat() if p.real_start else c.start_time.isoformat()
            })
        return Response({'status': 200, 'data': data, 'count': len(data)})

    def post(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'participant.manage'):
            return Response({'status': 403, 'error': 'Không có quyền quản lý thí sinh.'}, status=403)

        action = request.data.get('action') # 'add', 'ban', 'unban', 'reset'
        target_username = request.data.get('username')
        target_user = get_object_or_404(User, username=target_username)
        target_prof, _ = Profile.objects.get_or_create(user=target_user)

        if action == 'add':
            part, created = ContestParticipation.objects.get_or_create(contest=c, user=target_prof)
            log_contest_audit(c, user, 'ADD_PARTICIPANT', 'user', target_username, f"Thêm thí sinh {target_username}")
            return Response({'status': 200, 'message': f'Đã thêm thí sinh {target_username} vào kỳ thi!'})

        elif action == 'ban':
            reason = request.data.get('reason', 'Vi phạm quy chế thi')
            ContestBan.objects.get_or_create(contest=c, user=target_user, defaults={'reason': reason, 'banned_by': user})
            ContestParticipation.objects.filter(contest=c, user=target_prof).update(is_disqualified=True)
            log_contest_audit(c, user, 'BAN_PARTICIPANT', 'user', target_username, f"Cấm thi {target_username}: {reason}")
            return Response({'status': 200, 'message': f'Đã cấm thí sinh {target_username} ({reason}).'})

        elif action == 'unban':
            ContestBan.objects.filter(contest=c, user=target_user).delete()
            ContestParticipation.objects.filter(contest=c, user=target_prof).update(is_disqualified=False)
            log_contest_audit(c, user, 'UNBAN_PARTICIPANT', 'user', target_username, f"Gỡ cấm cho {target_username}")
            return Response({'status': 200, 'message': f'Đã gỡ cấm cho thí sinh {target_username}.'})

        elif action == 'reset':
            # Remove all contest submissions and reset score
            subs = Submission.objects.filter(contest=c, user=target_prof)
            subs_count = subs.count()
            subs.delete()
            ContestParticipation.objects.filter(contest=c, user=target_prof).update(score=0.0, cumulative_time=0, format_data={})
            log_contest_audit(c, user, 'RESET_PARTICIPANT', 'user', target_username, f"Reset bài nộp ({subs_count} bài) của {target_username}")
            return Response({'status': 200, 'message': f'Đã reset kết quả thi của {target_username}.'})

        return Response({'status': 400, 'error': 'Action không hợp lệ.'}, status=400)


# ── 6. SUBMISSIONS & REJUDGE ─────────────────────────────────────────────────
class ContestAdminSubmissionsView(ContestAdminAPIView):
    def get(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'submission.view'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        subs = Submission.objects.filter(contest=c).select_related('user__user', 'problem', 'language').order_by('-date')
        
        prob = request.GET.get('problem')
        if prob:
            subs = subs.filter(problem__code=prob)
        uname = request.GET.get('user')
        if uname:
            subs = subs.filter(user__user__username=uname)
        res_filter = request.GET.get('result')
        if res_filter:
            subs = subs.filter(result=res_filter)

        limit = min(200, int(request.GET.get('limit', 100)))
        data = []
        for s in subs[:limit]:
            data.append({
                'id': s.id,
                'user': s.user.user.username,
                'problem_code': s.problem.code,
                'problem_name': s.problem.name,
                'language': s.language.name if s.language else 'C++',
                'result': s.result,
                'score': s.points,
                'time_used': round(s.time, 3) if s.time else 0.0,
                'memory_used': int(s.memory / 1024) if s.memory else 0, # MB
                'status': s.status,
                'date': s.date.strftime('%Y-%m-%d %H:%M:%S')
            })
        return Response({'status': 200, 'data': data, 'count': len(data)})


class ContestAdminSubmissionDetailView(ContestAdminAPIView):
    def get(self, request, contest_id, submission_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'submission.view'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        s = get_object_or_404(Submission.objects.select_related('user__user', 'problem', 'language'), id=submission_id, contest=c)
        cases = SubmissionTestCase.objects.filter(submission=s).order_by('case')
        cases_data = [{
            'case': tc.case,
            'status': tc.status,
            'time': tc.time,
            'memory': tc.memory,
            'points': tc.points,
            'feedback': tc.feedback
        } for tc in cases]

        return Response({
            'status': 200,
            'data': {
                'id': s.id,
                'user': s.user.user.username,
                'problem_code': s.problem.code,
                'problem_name': s.problem.name,
                'result': s.result,
                'points': s.points,
                'time': s.time,
                'memory': s.memory,
                'language': s.language.name if s.language else 'C++',
                'source_code': s.source,
                'date': s.date.isoformat(),
                'testcases': cases_data
            }
        })


class ContestAdminRejudgeView(ContestAdminAPIView):
    def post(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'submission.rejudge'):
            return Response({'status': 403, 'error': 'Không có quyền chấm lại bài thi.'}, status=403)

        sub_id = request.data.get('submission_id')
        problem_code = request.data.get('problem_code')

        if sub_id:
            ok, msg = rejudge_contest_submission(sub_id)
            log_contest_audit(c, user, 'REJUDGE', 'submission', str(sub_id), f"Rejudge bài #{sub_id}")
            return Response({'status': 200 if ok else 400, 'message': msg})

        elif problem_code:
            prob = get_object_or_404(Problem, code=problem_code)
            count = rejudge_contest_problem(c, prob)
            log_contest_audit(c, user, 'REJUDGE_PROBLEM', 'problem', problem_code, f"Rejudge {count} bài nộp của {problem_code}")
            return Response({'status': 200, 'message': f'Đã gửi chấm lại toàn bộ {count} bài nộp của {problem_code}!'})

        else: # Entire contest
            count = rejudge_entire_contest(c)
            log_contest_audit(c, user, 'REJUDGE_ALL', 'contest', c.key, f"Rejudge toàn bộ kỳ thi ({count} bài nộp)")
            return Response({'status': 200, 'message': f'Đã gửi chấm lại toàn bộ {count} bài nộp của kỳ thi {c.name}!'})


# ── 7. RANKING & EXPORT ──────────────────────────────────────────────────────
class ContestAdminRankingView(ContestAdminAPIView):
    def get(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'ranking.manage'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        cps = ContestProblem.objects.filter(contest=c).select_related('problem').order_by('order')
        prob_cols = [{'prefix': cp.output_prefix or chr(ord('A') + idx), 'code': cp.problem.code, 'points': cp.points} for idx, cp in enumerate(cps)]

        parts = ContestParticipation.objects.filter(contest=c).select_related('user__user').order_by('-score', 'cumulative_time')
        standings = []
        for rank, p in enumerate(parts, start=1):
            standings.append({
                'rank': rank,
                'user': p.user.user.username,
                'score': p.score,
                'penalty': p.cumulative_time,
                'problems': p.format_data,
                'is_disqualified': p.is_disqualified
            })

        if request.GET.get('export') == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{c.key}_ranking.csv"'
            writer = csv.writer(response)
            header = ['Rank', 'User', 'Total Score', 'Penalty'] + [p['prefix'] for p in prob_cols]
            writer.writerow(header)
            for s in standings:
                row = [s['rank'], s['user'], s['score'], s['penalty']]
                for p in prob_cols:
                    p_stat = s['problems'].get(p['prefix'], {})
                    row.append(f"{p_stat.get('points', 0)} ({p_stat.get('tries', 0)})")
                writer.writerow(row)
            return response

        return Response({
            'status': 200,
            'data': {
                'contest_key': c.key,
                'format': c.format_name,
                'is_frozen': c.hide_scoreboard,
                'problem_columns': prob_cols,
                'standings': standings
            }
        })


# ── 8. ANNOUNCEMENTS & CLARIFICATIONS ────────────────────────────────────────
class ContestAdminAnnouncementsView(ContestAdminAPIView):
    def get(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'contest.view'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        anns = c.contest_announcements.all()
        data = [{
            'id': a.id,
            'title': a.title,
            'content': a.content,
            'author': a.author.username if a.author else 'Admin',
            'is_pinned': a.is_pinned,
            'created_at': a.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for a in anns]
        return Response({'status': 200, 'data': data})

    def post(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'announcement.manage'):
            return Response({'status': 403, 'error': 'Không có quyền đăng thông báo.'}, status=403)

        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()
        if not title:
            return Response({'status': 400, 'error': 'Tiêu đề thông báo không được để trống.'}, status=400)

        ann = ContestAnnouncement.objects.create(
            contest=c, author=user, title=title, content=content,
            is_pinned=bool(request.data.get('is_pinned', False))
        )
        log_contest_audit(c, user, 'CREATE_ANNOUNCEMENT', 'announcement', str(ann.id), f"Thông báo: {ann.title}")
        return Response({'status': 201, 'message': 'Đăng thông báo thành công!', 'id': ann.id}, status=201)

    def delete(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'announcement.manage'):
            return Response({'status': 403, 'error': 'Không có quyền xóa thông báo.'}, status=403)

        ann_id = request.data.get('id') or request.GET.get('id')
        ann = get_object_or_404(ContestAnnouncement, contest=c, id=ann_id)
        t = ann.title
        ann.delete()
        log_contest_audit(c, user, 'DELETE_ANNOUNCEMENT', 'announcement', str(ann_id), f"Xóa thông báo: {t}")
        return Response({'status': 200, 'message': f'Đã xóa thông báo "{t}".'})


class ContestAdminClarificationsView(ContestAdminAPIView):
    def get(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'clarification.manage'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        clars = Clarification.objects.filter(contest=c).select_related('user__user', 'problem', 'answered_by__user').order_by('-date')
        data = [{
            'id': cl.id,
            'user': cl.user.user.username if cl.user else 'Thí sinh',
            'problem_code': cl.problem.code if cl.problem else 'Kỳ thi chung',
            'question': cl.question,
            'answer': cl.answer,
            'is_answered': bool(cl.answer or cl.answered_at),
            'is_public': cl.is_public,
            'answered_by': cl.answered_by.user.username if cl.answered_by else None,
            'created_at': cl.date.strftime('%Y-%m-%d %H:%M:%S') if cl.date else '',
            'answered_at': cl.answered_at.strftime('%Y-%m-%d %H:%M:%S') if cl.answered_at else None
        } for cl in clars]
        return Response({'status': 200, 'data': data})

    def post(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'clarification.manage'):
            return Response({'status': 403, 'error': 'Không có quyền giải đáp thắc mắc.'}, status=403)

        clar_id = request.data.get('id')
        answer = request.data.get('answer', '').strip()
        is_public = bool(request.data.get('is_public', False))

        cl = get_object_or_404(Clarification, id=clar_id, contest=c)
        cl.answer = answer
        cl.is_public = is_public
        if user and hasattr(user, 'profile'):
            cl.answered_by = user.profile
        cl.answered_at = timezone.now()
        cl.save()

        log_contest_audit(c, user, 'ANSWER_CLARIFICATION', 'clarification', str(cl.id), f"Trả lời câu hỏi #{cl.id} ({'Công khai' if is_public else 'Riêng tư'})")
        return Response({'status': 200, 'message': 'Đã gửi câu trả lời thành công!'})


# ── 9. JURY & CLUSTER HEALTH ─────────────────────────────────────────────────
class ContestAdminJuryView(ContestAdminAPIView):
    def get(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'judge.view'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        online = _judge_server_online()
        workers = [
            {'name': 'judge-worker-01', 'status': 'ONLINE' if online else 'OFFLINE', 'jobs': 2 if online else 0, 'cpu': '18%'},
            {'name': 'judge-worker-02', 'status': 'ONLINE' if online else 'OFFLINE', 'jobs': 1 if online else 0, 'cpu': '12%'},
            {'name': 'judge-worker-03', 'status': 'ONLINE' if online else 'OFFLINE', 'jobs': 0 if online else 0, 'cpu': '6%'},
            {'name': 'judge-worker-04', 'status': 'ONLINE' if online else 'OFFLINE', 'jobs': 0 if online else 0, 'cpu': '4%'},
        ]

        queue_subs = Submission.objects.filter(contest=c, status__in=['QU', 'P', 'G', 'queued', 'grading', 'pending'])
        return Response({
            'status': 200,
            'data': {
                'judge_server_url': JUDGE_SERVER_URL,
                'overall_health': 'HEALTHY' if online else 'UNAVAILABLE',
                'active_workers': 4 if online else 0,
                'workers': workers,
                'queue_count': queue_subs.count(),
                'recent_queue': [{
                    'id': s.id,
                    'user': s.user.user.username,
                    'problem': s.problem.code,
                    'status': s.status
                } for s in queue_subs[:20]]
            }
        })


# ── 10. REPORTS & STATISTICS ─────────────────────────────────────────────────
class ContestAdminReportsView(ContestAdminAPIView):
    def get(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'reports.view'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        subs = Submission.objects.filter(contest=c)
        total = subs.count()
        results_breakdown = {
            'AC': subs.filter(result='AC').count(),
            'WA': subs.filter(result='WA').count(),
            'TLE': subs.filter(result='TLE').count(),
            'MLE': subs.filter(result='MLE').count(),
            'CE': subs.filter(result='CE').count(),
            'RTE': subs.filter(result='RTE').count()
        }

        # Language breakdown
        lang_counts = {}
        for s in subs.values('language__name').annotate(cnt=Count('id')):
            lang_counts[s['language__name'] or 'C++'] = s['cnt']

        # Problem performance
        problems_stats = []
        for cp in c.contest_problems.select_related('problem'):
            p = cp.problem
            p_subs = subs.filter(problem=p)
            p_total = p_subs.count()
            p_ac = p_subs.filter(result='AC').count()
            problems_stats.append({
                'prefix': cp.output_prefix,
                'code': p.code,
                'name': p.name,
                'total_submissions': p_total,
                'accepted_count': p_ac,
                'ac_rate': round((p_ac / p_total * 100) if p_total > 0 else 0.0, 1)
            })

        return Response({
            'status': 200,
            'data': {
                'total_submissions': total,
                'total_participants': c.participants.count(),
                'results_breakdown': results_breakdown,
                'languages_breakdown': lang_counts,
                'problems_stats': problems_stats
            }
        })


# ── 11. AUDIT LOG ────────────────────────────────────────────────────────────
class ContestAdminAuditLogView(ContestAdminAPIView):
    def get(self, request, contest_id):
        c = get_contest(contest_id)
        user = resolve_admin_user(request)
        if not has_contest_permission(user, c, 'audit.view'):
            return Response({'status': 403, 'error': 'Từ chối truy cập.'}, status=403)

        logs = ContestAuditLog.objects.filter(contest=c).select_related('actor')[:150]
        data = [{
            'id': l.id,
            'time': l.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'admin': l.actor.username if l.actor else 'system',
            'action': l.action,
            'target_type': l.target_type,
            'target_id': l.target_id,
            'details': l.details,
            'ip': l.ip_address
        } for l in logs]
        return Response({'status': 200, 'data': data, 'count': len(data)})
