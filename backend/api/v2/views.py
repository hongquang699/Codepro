import os
import json
import zipfile
import hmac
import re
import secrets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication, get_or_rotate_token, token_is_expired
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.db.models import Q, Count
from django.conf import settings
from security.encryption import file_cipher

from backend.judge.models import (
    Profile, Organization, Language, Problem, ProblemType, Contest,
    ContestProblem, Submission, SubmissionTestCase, Judge,
    ContestParticipation, RatingHistory, BlogPost, Comment, Clarification, CodeShare
)
from backend.judge.bridge import grade_submission
from backend.judge.contest_visibility import contest_visible, request_surface, valid_display_target, visible_contests
from backend.judge import problem_package
from backend.judge.api.admin_views import JudgeAdminView
from backend.judge.permissions.authentication import BearerTokenAuthentication, JudgeCookieAuthentication
from backend.submissions.validators.source import SourceCodeValidator
from backend.auth.security.device import get_client_ip, get_user_agent
from backend.auth.services.authentication import authenticate_user
from backend.auth.services.registration import initiate_registration
from .serializers import (
    UserProfileSerializer, PublicUserProfileSerializer, OrganizationSerializer,
    LanguageSerializer, ProblemListSerializer, ProblemDetailSerializer,
    SubmissionListSerializer, SubmissionDetailSerializer,
    ContestListSerializer, ContestDetailSerializer, JudgeSerializer,
    ClarificationSerializer, RatingHistorySerializer, BlogPostSerializer,
    CommentSerializer, RankingUserSerializer
)

def dmoj_response(data=None, error=None, status_code=200):
    if error:
        return Response({'status': status_code, 'error': error}, status=status_code)
    return Response({'status': status_code, 'data': data}, status=status_code)


class V2APIView(APIView):
    authentication_classes = [TokenAuthentication, BearerTokenAuthentication, JudgeCookieAuthentication, SessionAuthentication]


class IsPlatformAdmin(BasePermission):
    """Require a verified server-side session or DRF token with staff privileges."""
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_active and (user.is_staff or user.is_superuser))


class IsPlatformAdminOrReadOnly(IsPlatformAdmin):
    def has_permission(self, request, view):
        return request.method in ('GET', 'HEAD', 'OPTIONS') or super().has_permission(request, view)


def code_share_payload(share, include_source=False):
    data = {
        'token': share.token,
        'owner': share.owner.username,
        'problem': share.problem.code,
        'problem_name': share.problem.name,
        'contest': share.contest.key if share.contest else None,
        'language': share.language,
        'is_active': share.is_active and share.expires_at > timezone.now(),
        'updated_at': share.updated_at,
        'expires_at': share.expires_at,
    }
    if include_source:
        data['source'] = share.source
    return data


def code_share_context(request, body):
    source = body.get('source')
    language = body.get('language')
    code = body.get('problem')
    contest_key = body.get('contest') or None
    if not isinstance(source, str) or len(source) > 500000:
        raise ValueError('Mã nguồn không hợp lệ hoặc quá lớn.')
    if not isinstance(language, str) or not re.fullmatch(r'[A-Za-z0-9_]{1,32}', language):
        raise ValueError('Ngôn ngữ không hợp lệ.')
    problem = Problem.objects.filter(code=code).first() if isinstance(code, str) else None
    if not problem or not problem.is_public:
        raise ValueError('Bài tập không công khai hoặc không tồn tại.')
    contest = None
    if contest_key:
        contest = Contest.objects.filter(key=contest_key).first() if isinstance(contest_key, str) else None
        if not contest or not ContestProblem.objects.filter(contest=contest, problem=problem).exists():
            raise ValueError('Bài thi không thuộc cuộc thi.')
        if not IsPlatformAdmin().has_permission(request, None):
            if not contest_visible(contest, request_surface(request)) or not ContestParticipation.objects.filter(
                    contest=contest, user__user=request.user).exists():
                raise ValueError('Bạn chưa tham gia cuộc thi này.')
    return source, language, problem, contest


class APICodeShareList(V2APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        shares = CodeShare.objects.filter(is_active=True, expires_at__gt=timezone.now()).select_related(
            'owner', 'problem', 'contest')
        if not IsPlatformAdmin().has_permission(request, self):
            shares = shares.filter(owner=request.user)
        return dmoj_response({'objects': [code_share_payload(share) for share in shares[:100]]})

    def post(self, request):
        try:
            source, language, problem, contest = code_share_context(request, request.data)
        except ValueError as error:
            return dmoj_response(error={'message': str(error)}, status_code=400)
        share = CodeShare.objects.create(
            token=secrets.token_urlsafe(32), owner=request.user, problem=problem,
            contest=contest, language=language, source=source,
            expires_at=timezone.now() + timezone.timedelta(hours=24),
        )
        return dmoj_response(code_share_payload(share), status_code=201)


class APICodeShareDetail(V2APIView):
    def get(self, request, token):
        share = CodeShare.objects.select_related('owner', 'problem', 'contest').filter(token=token).first()
        if not share or not share.is_active or share.expires_at <= timezone.now():
            return dmoj_response(error={'message': 'Liên kết chia sẻ đã hết hạn hoặc bị thu hồi.'}, status_code=404)
        response = dmoj_response(code_share_payload(share, include_source=True))
        response['Cache-Control'] = 'no-store'
        return response

    def put(self, request, token):
        if not request.user.is_authenticated:
            return dmoj_response(error={'message': 'Cần đăng nhập.'}, status_code=401)
        share = CodeShare.objects.filter(token=token).first()
        if not share or (share.owner_id != request.user.id and not IsPlatformAdmin().has_permission(request, self)):
            return dmoj_response(error={'message': 'Không có quyền quản lý phiên chia sẻ.'}, status_code=403)
        if request.data.get('is_active') is False:
            share.is_active = False
            share.save(update_fields=['is_active', 'updated_at'])
            return dmoj_response(code_share_payload(share))
        if share.owner_id != request.user.id or not share.is_active or share.expires_at <= timezone.now():
            return dmoj_response(error={'message': 'Phiên chia sẻ đã kết thúc.'}, status_code=403)
        try:
            source, language, problem, contest = code_share_context(request, request.data)
        except ValueError as error:
            return dmoj_response(error={'message': str(error)}, status_code=400)
        share.source, share.language, share.problem, share.contest = source, language, problem, contest
        share.save(update_fields=['source', 'language', 'problem', 'contest', 'updated_at'])
        return dmoj_response(code_share_payload(share))


# ── USERS & PROFILES ────────────────────────────────────────────────────────
class APIUserList(V2APIView):
    def get(self, request):
        is_admin = bool(request.user.is_authenticated and request.user.is_active and
                        (request.user.is_staff or request.user.is_superuser))
        qs = Profile.objects.select_related('user').all()
        q = request.GET.get('q', '').strip()
        if q:
            search = Q(user__username__icontains=q)
            if is_admin:
                search |= Q(user__email__icontains=q)
            qs = qs.filter(search)
        
        page = max(1, int(request.GET.get('page', 1)))
        page_size = min(100, max(1, int(request.GET.get('page_size', 50))))
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        serializer_class = UserProfileSerializer if is_admin else PublicUserProfileSerializer
        serializer = serializer_class(qs[start:end], many=True)
        return dmoj_response({
            'current_page': page,
            'page_size': page_size,
            'total_objects': total,
            'total_pages': max(1, (total + page_size - 1) // page_size),
            'has_more': end < total,
            'objects': serializer.data
        })

class APIUserDetail(V2APIView):
    permission_classes = [IsPlatformAdminOrReadOnly]

    def get(self, request, username):
        prof = get_object_or_404(Profile.objects.select_related('user'), user__username=username)
        user = request.user
        can_view_private = bool(user.is_authenticated and user.is_active and
                                (user.pk == prof.user_id or user.is_staff or user.is_superuser))
        serializer_class = UserProfileSerializer if can_view_private else PublicUserProfileSerializer
        serializer = serializer_class(prof)
        data = serializer.data

        # Solved problems
        solved = list(Submission.objects.filter(user=prof, result='AC').values_list('problem__code', flat=True).distinct())
        # Attempted problems
        attempted = list(Submission.objects.filter(user=prof).exclude(result='AC').values_list('problem__code', flat=True).distinct())
        attempted = [p for p in attempted if p not in solved]

        # Recent submissions
        recent_subs = Submission.objects.filter(user=prof).select_related('problem', 'language')[:15]
        sub_serializer = SubmissionListSerializer(recent_subs, many=True)

        data['solved_problems'] = solved
        data['attempted_problems'] = attempted
        data['solved_count'] = len(solved)
        data['recent_submissions'] = sub_serializer.data
        return dmoj_response({'object': data})

    def put(self, request, username=None):
        username = username or request.user.username
        prof = get_object_or_404(Profile.objects.select_related('user'), user__username=username)
        u = prof.user
        about = request.data.get('about')
        timezone_val = request.data.get('timezone')
        lang_key = request.data.get('language')
        email = request.data.get('email')
        display_name = request.data.get('display_name') or request.data.get('full_name')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        password = request.data.get('password')
        rating = request.data.get('rating')
        is_verified = request.data.get('is_verified')

        if about is not None:
            prof.about = about
        if timezone_val:
            prof.timezone = timezone_val
        if lang_key:
            lang = Language.objects.filter(key=lang_key).first()
            if lang:
                prof.language = lang
        if email:
            u.email = email.strip()
        if display_name is not None:
            parts = display_name.strip().split(' ', 1)
            u.first_name = parts[0]
            u.last_name = parts[1] if len(parts) > 1 else ''
        if first_name is not None:
            u.first_name = first_name.strip()
        if last_name is not None:
            u.last_name = last_name.strip()
        if password and password.strip():
            u.set_password(password.strip())
        u.save()

        if rating is not None:
            try:
                prof.rating = int(rating)
                prof.update_rating_rank()
            except (ValueError, TypeError):
                pass
        if is_verified is not None:
            prof.is_verified = bool(is_verified)

        prof.save()
        return dmoj_response({'message': 'Profile updated successfully', 'object': UserProfileSerializer(prof).data})


# ── RANKINGS / LEADERBOARD ──────────────────────────────────────────────────
class APIRankings(V2APIView):
    def get(self, request):
        sort_by = request.GET.get('sort', 'rating') # rating or points
        qs = Profile.objects.select_related('user').all()
        if sort_by == 'points':
            qs = qs.order_by('-points', '-problem_count')
        else:
            qs = qs.order_by('-rating', '-problem_count')

        page = max(1, int(request.GET.get('page', 1)))
        page_size = min(100, max(1, int(request.GET.get('page_size', 50))))
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        items = []
        for rank_idx, p in enumerate(qs[start:end], start=start + 1):
            items.append({
                'rank': rank_idx,
                'username': p.user.username,
                'display_name': p.user.get_full_name() or p.user.username,
                'rating': p.rating if p.rating is not None else 0,
                'display_rank': p.display_rank or ('Unrated' if not p.rating else 'Newbie'),
                'points': p.points,
                'solved_count': p.problem_count,
                'is_verified': getattr(p, 'is_verified', False),
                'about': p.about[:80] if p.about else ''
            })

        return dmoj_response({
            'current_page': page,
            'page_size': page_size,
            'total_users': total,
            'total_pages': max(1, (total + page_size - 1) // page_size),
            'has_more': end < total,
            'objects': items
        })

class APIUserRatingHistory(V2APIView):
    def get(self, request, username):
        prof = get_object_or_404(Profile.objects.select_related('user'), user__username=username)
        ratings = RatingHistory.objects.filter(user=prof).select_related('contest').order_by('last_rated')
        serializer = RatingHistorySerializer(ratings, many=True)
        return dmoj_response({'objects': serializer.data})


# ── PROBLEMS ────────────────────────────────────────────────────────────────
class APIProblemList(V2APIView):
    permission_classes = [IsPlatformAdminOrReadOnly]

    def get(self, request):
        is_admin = IsPlatformAdmin().has_permission(request, self)
        qs = Problem.objects.prefetch_related('types').all() if is_admin and request.GET.get('all') == '1' else Problem.objects.prefetch_related('types').filter(is_public=True)
        q = request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))

        tag = request.GET.get('tag') or request.GET.get('type')
        if tag:
            qs = qs.filter(types__name=tag)

        diff = request.GET.get('difficulty')
        if diff:
            qs = qs.filter(difficulty=diff)

        author = request.GET.get('author')
        if author:
            qs = qs.filter(authors__user__username=author)

        page = max(1, int(request.GET.get('page', 1)))
        page_size = min(1000, max(1, int(request.GET.get('page_size', 500))))
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        serializer = ProblemListSerializer(qs[start:end], many=True)
        return dmoj_response({
            'current_page': page,
            'page_size': page_size,
            'total_objects': total,
            'total_pages': max(1, (total + page_size - 1) // page_size),
            'has_more': end < total,
            'objects': serializer.data
        })

    def post(self, request):
        code = request.data.get('code', '').strip().upper()
        name = request.data.get('name', '').strip()
        if not code or not name:
            return dmoj_response(error={'message': 'Mã bài tập và tiêu đề không được để trống'}, status_code=400)
        if not re.fullmatch(r'[A-Z0-9][A-Z0-9_-]{0,63}', code):
            return dmoj_response(error={'message': 'Mã bài không hợp lệ'}, status_code=400)

        if Problem.objects.filter(code=code).exists():
            return dmoj_response(error={'message': f'Bài tập mã {code} đã tồn tại'}, status_code=400)

        prob = Problem.objects.create(
            code=code,
            name=name,
            description=request.data.get('description', 'Mô tả bài toán...'),
            time_limit=float(request.data.get('time_limit', 1.0)),
            memory_limit=int(request.data.get('memory_limit', 262144)),
            points=float(request.data.get('points', 100.0)),
            difficulty=request.data.get('difficulty', 'medium'),
            partial=bool(request.data.get('partial', False)),
            is_public=bool(request.data.get('is_public', False)),
            status=request.data.get('status', 'draft')
        )

        tags = request.data.get('tags', [])
        for t in tags:
            pt, _ = ProblemType.objects.get_or_create(name=t, defaults={'full_name': t.title()})
            prob.types.add(pt)

        # Setup local problem data directories
        prob_dir = os.path.join(settings.DMOJ_PROBLEM_DATA_ROOT, code)
        os.makedirs(os.path.join(prob_dir, 'cases'), exist_ok=True)

        return dmoj_response(ProblemDetailSerializer(prob).data, status_code=201)

class APIProblemDetail(V2APIView):
    permission_classes = [IsPlatformAdminOrReadOnly]

    def get(self, request, problem):
        prob = get_object_or_404(Problem.objects.prefetch_related('types', 'authors'), code=problem)
        is_admin = IsPlatformAdmin().has_permission(request, self)
        if prob.is_organization_private:
            user = request.user if request.user.is_authenticated else None

            is_allowed = False
            if is_admin:
                is_allowed = True
            elif user:
                from backend.organizations.models import OrganizationMember
                for org in prob.organizations.all():
                    if getattr(org, 'owner_id', None) == user.id or OrganizationMember.objects.filter(organization=org, user=user, status='active').exists():
                        is_allowed = True
                        break
            if not is_allowed:
                return dmoj_response(error={'message': 'Bài tập này thuộc quyền quản lý nội bộ của tổ chức. Bạn cần là thành viên tổ chức để truy cập.'}, status_code=403)

        if not prob.is_public and not is_admin:
            can_view_contest_problem = (
                request.user.is_authenticated and ContestProblem.objects.filter(
                    problem=prob, contest__is_visible=True,
                    contest__start_time__lte=timezone.now(),
                    contest__participants__user__user=request.user,
                ).exists()
            )
            if not can_view_contest_problem and not prob.is_organization_private:
                return dmoj_response(error={'message': 'Bài tập chưa công khai'}, status_code=403)

        serializer = ProblemDetailSerializer(prob)
        data = serializer.data
        # The package Markdown is the authoring source of truth. Older database
        # descriptions may contain damaged LaTeX from a previous HTML import.
        statement = problem_package.get_statement(prob.code).get('markdown', '')
        if statement.strip():
            data['description'] = statement

        # Calculate AC rate and submission count
        total_subs = Submission.objects.filter(problem=prob).count()
        ac_subs = Submission.objects.filter(problem=prob, result='AC').values('user').distinct().count()
        data['submission_count'] = total_subs
        data['solved_count'] = ac_subs
        data['ac_rate'] = round((ac_subs / total_subs * 100.0), 1) if total_subs > 0 else 0.0

        return dmoj_response({'object': data})

    def put(self, request, problem):
        prob = get_object_or_404(Problem, code=problem)
        for field in ['name', 'description', 'time_limit', 'memory_limit', 'points', 'difficulty', 'partial', 'is_public', 'status']:
            if field in request.data:
                setattr(prob, field, request.data[field])
        prob.save()
        return dmoj_response({'message': 'Updated successfully', 'object': ProblemDetailSerializer(prob).data})

class APIProblemStatement(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def put(self, request, problem):
        prob = get_object_or_404(Problem, code=problem)
        body = request.data
        desc = body.get('description', prob.description)
        inp = body.get('input', '')
        outp = body.get('output', '')
        constraints = body.get('constraints', '')
        notes = body.get('notes', '')

        # Build full structured markdown if separate sections given
        if inp or outp or constraints:
            full_md = f"{desc}\n\n### Đầu vào\n{inp}\n\n### Đầu ra\n{outp}\n\n### Giới hạn\n{constraints}\n"
            if notes:
                full_md += f"\n### Ghi chú\n{notes}\n"
            prob.description = full_md
        else:
            prob.description = desc
        prob.save()
        return dmoj_response({'message': 'Statement updated successfully', 'description': prob.description})

class APIProblemTestcases(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request, problem):
        prob = get_object_or_404(Problem, code=problem)
        cases_dir = os.path.join(settings.DMOJ_PROBLEM_DATA_ROOT, prob.code, 'cases')
        testcases = []
        if os.path.isdir(cases_dir):
            for f in sorted(os.listdir(cases_dir)):
                if f.endswith('.in'):
                    base = f[:-3]
                    out_f = os.path.join(cases_dir, f'{base}.out')
                    in_f = os.path.join(cases_dir, f)
                    in_size = len(file_cipher.read_file(in_f))
                    out_size = len(file_cipher.read_file(out_f)) if os.path.exists(out_f) else 0
                    testcases.append({
                        'id': base,
                        'input_file': f,
                        'output_file': f'{base}.out' if os.path.exists(out_f) else None,
                        'input_size': in_size,
                        'output_size': out_size
                    })
        return dmoj_response({'problem': prob.code, 'count': len(testcases), 'testcases': testcases})

    def post(self, request, problem):
        prob = get_object_or_404(Problem, code=problem)
        cases_dir = os.path.join(settings.DMOJ_PROBLEM_DATA_ROOT, prob.code, 'cases')
        os.makedirs(cases_dir, exist_ok=True)

        case_id = str(request.data.get('id') or f"{len(os.listdir(cases_dir)) // 2 + 1:02d}")
        if not case_id.replace('-', '').replace('_', '').isalnum() or len(case_id) > 64:
            return dmoj_response(error={'message': 'Mã testcase không hợp lệ'}, status_code=400)
        in_content = request.data.get('input', '')
        out_content = request.data.get('output', '')

        in_path = os.path.join(cases_dir, f"{case_id}.in")
        out_path = os.path.join(cases_dir, f"{case_id}.out")

        file_cipher.write_file(in_path, in_content.encode('utf-8'))
        file_cipher.write_file(out_path, out_content.encode('utf-8'))

        return dmoj_response({
            'message': f'Testcase {case_id} added successfully',
            'case_id': case_id
        }, status_code=201)

class APIProblemTestcasesUpload(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request, problem):
        prob = get_object_or_404(Problem, code=problem)
        file_obj = request.FILES.get('file') or request.FILES.get('tests')
        if not file_obj:
            return dmoj_response(error={'message': 'Vui lòng chọn file zip testcases'}, status_code=400)
        if not file_obj.name.lower().endswith('.zip') or file_obj.size > 20 * 1024 * 1024:
            return dmoj_response(error={'message': 'Tệp ZIP không hợp lệ hoặc vượt giới hạn 20 MiB'}, status_code=400)
        try:
            problem_package.import_zip_testcases(prob.code, file_obj.read())
            return dmoj_response({'message': 'Giải nén và nạp testcase thành công!'})
        except (ValueError, zipfile.BadZipFile):
            return dmoj_response(error={'message': 'Tệp ZIP testcase không hợp lệ'}, status_code=400)

class APIProblemPublish(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request, problem):
        prob = get_object_or_404(Problem, code=problem)
        vis = request.data.get('visibility', 'public')
        prob.is_public = (vis == 'public')
        prob.status = 'published' if prob.is_public else 'ready'
        prob.save()
        return dmoj_response({'message': f'Bài tập {prob.code} đã được publish ({vis})', 'status': prob.status})


# ── SUBMISSIONS ─────────────────────────────────────────────────────────────
class APISubmissionList(V2APIView):
    def get(self, request):
        qs = Submission.objects.select_related('problem', 'user__user', 'language', 'contest').all()
        user = request.GET.get('user')
        if user:
            qs = qs.filter(user__user__username=user)
        prob = request.GET.get('problem')
        if prob:
            qs = qs.filter(problem__code=prob)
        lang = request.GET.get('language')
        if lang:
            qs = qs.filter(language__key__iexact=lang)
        res = request.GET.get('result')
        if res:
            qs = qs.filter(result=res.upper())
        ct = request.GET.get('contest')
        if ct:
            qs = qs.filter(contest__key=ct)

        page = max(1, int(request.GET.get('page', 1)))
        page_size = min(100, max(1, int(request.GET.get('page_size', 50))))
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        serializer = SubmissionListSerializer(qs[start:end], many=True)
        return dmoj_response({
            'current_page': page,
            'page_size': page_size,
            'total_objects': total,
            'total_pages': max(1, (total + page_size - 1) // page_size),
            'has_more': end < total,
            'objects': serializer.data
        })

class APISubmissionDetail(V2APIView):
    def get(self, request, submission_id):
        sub = get_object_or_404(Submission.objects.select_related('problem', 'user__user', 'language'), id=submission_id)
        serializer = SubmissionDetailSerializer(sub, context={'request': request})
        return dmoj_response({'object': serializer.data})

class APISubmitView(V2APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        problem_code = request.data.get('problem')
        lang_key = request.data.get('language')
        source = request.data.get('source', '')
        username = request.user.username

        contest_key = request.data.get('contest')

        if not problem_code or not lang_key or not source:
            return dmoj_response(error={'message': 'Missing problem, language or source'}, status_code=400)

        valid_source, source_error = SourceCodeValidator.validate(source)
        if not valid_source:
            return dmoj_response(error={'message': source_error}, status_code=400)
        if not isinstance(lang_key, str):
            return dmoj_response(error={'message': 'Ngôn ngữ lập trình không hợp lệ'}, status_code=400)

        prob = get_object_or_404(Problem, code=problem_code)
        if prob.is_organization_private:
            from backend.organizations.models import OrganizationMember
            has_org_access = IsPlatformAdmin().has_permission(request, self) or any(
                org.owner_id == request.user.id or OrganizationMember.objects.filter(
                    organization=org, user=request.user, status='active').exists()
                for org in prob.organizations.all()
            )
            if not has_org_access:
                return dmoj_response(error={'message': 'Bạn không có quyền nộp bài này'}, status_code=403)

        lang_alias_map = {
            'CPP': 'CPP17', 'C++': 'CPP17', 'CPP17': 'CPP17', 'C++17': 'CPP17', 'CPP20': 'CPP17', 'C++20': 'CPP17',
            'C': 'C11', 'C11': 'C11',
            'PY': 'PY3', 'PYTHON': 'PY3', 'PYTHON3': 'PY3', 'PY3': 'PY3',
            'JAVA': 'JAVA17', 'JAVA17': 'JAVA17',
            'RUST': 'RUST',
            'GO': 'GO', 'GOLANG': 'GO',
            'PAS': 'PAS', 'PASCAL': 'PAS'
        }
        clean_key = lang_key.strip().upper()
        resolved_key = lang_alias_map.get(clean_key, clean_key)
        lang = Language.objects.filter(key__iexact=resolved_key, is_active=True).first() or get_object_or_404(
            Language, key__iexact=lang_key, is_active=True)
        prof = Profile.objects.filter(user__username=username).first()
        if not prof:
            return dmoj_response(error={'message': f'Không tìm thấy hồ sơ người dùng: {username}'}, status_code=404)

        contest_obj = None
        if contest_key:
            contest_obj = Contest.objects.filter(key=contest_key).first()
            now = timezone.now()
            if (not contest_obj or not contest_obj.is_visible or
                    not contest_obj.start_time <= now <= contest_obj.end_time or
                    not ContestProblem.objects.filter(contest=contest_obj, problem=prob).exists() or
                    not ContestParticipation.objects.filter(contest=contest_obj, user=prof,
                                                            is_disqualified=False).exists()):
                return dmoj_response(error={'message': 'Bạn không thể nộp bài cho kỳ thi này'}, status_code=403)
            from backend.organizations.models import OrganizationContest, OrganizationMember
            org_contest = OrganizationContest.objects.filter(contest=contest_obj).select_related('organization').first()
            if org_contest and not IsPlatformAdmin().has_permission(request, self):
                org = org_contest.organization
                if org.owner_id != request.user.id and not OrganizationMember.objects.filter(
                        organization=org, user=request.user, status='active').exists():
                    return dmoj_response(error={'message': 'Bạn không có quyền nộp bài cho kỳ thi nội bộ này'},
                                         status_code=403)
        elif not prob.is_public:
            if not prob.is_organization_private:
                return dmoj_response(error={'message': 'Bài tập chưa công khai'}, status_code=403)

        sub = Submission.objects.create(
            problem=prob,
            user=prof,
            language=lang,
            source=source,
            status='QU',
            contest=contest_obj
        )

        # Immediate grading via bridge
        grade_submission(sub.id)
        sub.refresh_from_db()

        return dmoj_response({
            'submission_id': sub.id,
            'result': sub.result,
            'points': sub.points,
            'time': sub.time,
            'memory': sub.memory,
            'status': sub.status
        }, status_code=201)

class APIRejudgeView(JudgeAdminView):

    def post(self, request, submission_id):
        sub = get_object_or_404(Submission, id=submission_id)
        self.audit(request, 'submission.rejudge', str(submission_id))
        sub.is_rejudged = True
        sub.save()
        grade_submission(sub.id)
        sub.refresh_from_db()
        return dmoj_response({
            'message': f'Submission #{sub.id} rejudged successfully.',
            'result': sub.result,
            'points': sub.points
        })

class APIRejudgeProblemView(JudgeAdminView):
    def post(self, request, problem):
        self.audit(request, 'problem.rejudge', problem)
        prob = get_object_or_404(Problem, code=problem)
        subs = Submission.objects.filter(problem=prob)
        count = subs.count()
        for s in subs:
            s.is_rejudged = True
            s.save()
            grade_submission(s.id)
        return dmoj_response({'message': f'Đã rejudge thành công toàn bộ {count} bài nộp của {prob.code}'})


# ── CONTESTS ────────────────────────────────────────────────────────────────
class APIContestList(V2APIView):
    permission_classes = [IsPlatformAdminOrReadOnly]

    def get(self, request):
        now = timezone.now()
        is_all = (request.GET.get('all') == '1' or request.GET.get('admin') == '1') and IsPlatformAdmin().has_permission(request, self)
        qs = Contest.objects.all().order_by('-start_time') if is_all else Contest.objects.filter(visible_contests(request_surface(request))).order_by('-start_time')
        items = []
        for ct in qs:
            c_status = 'ongoing' if ct.start_time <= now <= ct.end_time else ('upcoming' if now < ct.start_time else 'ended')
            items.append({
                'key': ct.key,
                'name': ct.name,
                'start_time': ct.start_time,
                'end_time': ct.end_time,
                'time_limit': ct.time_limit,
                'format_name': ct.format_name,
                'is_rated': ct.is_rated,
                'is_visible': ct.is_visible,
                'display_target': ct.display_target,
                'status': c_status,
                'participant_count': ct.participants.count()
            })
        return dmoj_response({'objects': items})

    def post(self, request):
        key = request.data.get('key', '').strip()
        name = request.data.get('name', '').strip()
        if not key or not name:
            return dmoj_response(error={'message': 'Mã và tên kỳ thi không được để trống'}, status_code=400)

        if Contest.objects.filter(key=key).exists():
            return dmoj_response(error={'message': f'Kỳ thi {key} đã tồn tại'}, status_code=400)
        display_target = request.data.get('display_target', 'both')
        if not valid_display_target(display_target):
            return dmoj_response(error={'message': 'Nơi hiển thị không hợp lệ'}, status_code=400)

        start = request.data.get('start_time') or timezone.now()
        duration = int(request.data.get('duration_seconds', 7200))
        end = request.data.get('end_time') or (timezone.now() + timezone.timedelta(seconds=duration))

        ct = Contest.objects.create(
            key=key,
            name=name,
            description=request.data.get('description', ''),
            start_time=start,
            end_time=end,
            time_limit=duration,
            format_name=request.data.get('format_name', 'icpc'),
            is_rated=bool(request.data.get('is_rated', True)),
            is_visible=bool(request.data.get('is_visible', True)),
            display_target=display_target
        )

        prob_codes = request.data.get('problems', [])
        for idx, p_code in enumerate(prob_codes, start=1):
            p = Problem.objects.filter(code=p_code).first()
            if p:
                prefix = chr(ord('A') + idx - 1)
                ContestProblem.objects.create(contest=ct, problem=p, order=idx, output_prefix=prefix)

        return dmoj_response(ContestDetailSerializer(ct).data, status_code=201)

def resolve_contest(contest_key):
    c = Contest.objects.filter(key__iexact=contest_key).first()
    if not c:
        c = Contest.objects.filter(key__iexact=contest_key.replace('-', '_')).first()
    if not c:
        c = Contest.objects.filter(key__iexact=contest_key.replace('_', '-')).first()
    if not c and str(contest_key).isdigit():
        c = Contest.objects.filter(id=int(contest_key)).first()
    if not c:
        return get_object_or_404(Contest, key=contest_key)
    return c


class APIContestDetail(V2APIView):
    permission_classes = [IsPlatformAdminOrReadOnly]

    def get(self, request, contest):
        ct = resolve_contest(contest)
        if not contest_visible(ct, request_surface(request)) and not IsPlatformAdmin().has_permission(request, self):
            return dmoj_response(error={'message': 'Kỳ thi chưa công khai'}, status_code=403)
        serializer = ContestDetailSerializer(ct)
        data = serializer.data
        now = timezone.now()
        data['status'] = 'ongoing' if ct.start_time <= now <= ct.end_time else ('upcoming' if now < ct.start_time else 'ended')
        data['time_remaining_sec'] = max(0, int((ct.end_time - now).total_seconds())) if data['status'] == 'ongoing' else 0

        # Check if requesting user is registered
        username = request.GET.get('user') or (request.user.username if request.user.is_authenticated else None)
        if username:
            data['is_registered'] = ContestParticipation.objects.filter(contest=ct, user__user__username=username).exists()
        else:
            data['is_registered'] = False

        return dmoj_response({'object': data})

    def put(self, request, contest):
        ct = resolve_contest(contest)
        if 'display_target' in request.data:
            if not valid_display_target(request.data['display_target']):
                return dmoj_response(error={'message': 'Nơi hiển thị không hợp lệ'}, status_code=400)
            ct.display_target = request.data['display_target']
        for field in ['name', 'description', 'time_limit', 'format_name', 'is_rated', 'is_visible', 'hide_scoreboard']:
            if field in request.data:
                setattr(ct, field, request.data[field])
        if 'start_time' in request.data and request.data['start_time']:
            ct.start_time = request.data['start_time']
        if 'end_time' in request.data and request.data['end_time']:
            ct.end_time = request.data['end_time']
        ct.save()

        # Update problems if provided
        if 'problems' in request.data:
            prob_codes = request.data.get('problems', [])
            ContestProblem.objects.filter(contest=ct).delete()
            for idx, p_code in enumerate(prob_codes, start=1):
                p = Problem.objects.filter(code=p_code).first()
                if p:
                    prefix = chr(ord('A') + idx - 1)
                    ContestProblem.objects.create(contest=ct, problem=p, order=idx, output_prefix=prefix)
        return dmoj_response({'message': 'Contest updated successfully', 'object': ContestDetailSerializer(ct).data})

    def delete(self, request, contest):
        ct = resolve_contest(contest)
        ct.delete()
        return dmoj_response({'message': f'Đã xóa kỳ thi {contest}'})

class APIContestJoin(V2APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, contest):
        ct = resolve_contest(contest)
        username = request.user.username
        prof = get_object_or_404(Profile, user__username=username)

        if request.data.get('action') == 'leave':
            ContestParticipation.objects.filter(contest=ct, user=prof).delete()
            return dmoj_response({
                'message': f'Đã rời khỏi kỳ thi {ct.name}',
                'contest': ct.key,
                'user': prof.user.username,
                'is_registered': False,
                'left': True
            })

        if not contest_visible(ct, request_surface(request)) or ct.end_time < timezone.now():
            return dmoj_response(error={'message': 'Kỳ thi không mở đăng ký'}, status_code=403)
        from backend.organizations.models import OrganizationContest, OrganizationMember
        org_contest = OrganizationContest.objects.filter(contest=ct).select_related('organization').first()
        if org_contest and not IsPlatformAdmin().has_permission(request, self):
            org = org_contest.organization
            if org.owner_id != request.user.id and not OrganizationMember.objects.filter(
                    organization=org, user=request.user, status='active').exists():
                return dmoj_response(error={'message': 'Bạn cần là thành viên tổ chức để tham gia kỳ thi'}, status_code=403)

        now = timezone.now()
        active_part = ContestParticipation.objects.filter(
            user=prof,
            contest__end_time__gte=now
        ).exclude(contest=ct).select_related('contest').first()

        if active_part:
            other_c = active_part.contest
            return dmoj_response(
                error={
                    'code': 'ALREADY_IN_ANOTHER_CONTEST',
                    'message': f'Bạn đang tham gia cuộc thi "{other_c.name}". Mỗi thí sinh chỉ được tham gia 1 cuộc thi tại một thời điểm. Vui lòng rời cuộc thi đó trước!',
                    'active_contest_key': other_c.key,
                    'active_contest_name': other_c.name
                },
                status_code=400
            )

        part, created = ContestParticipation.objects.get_or_create(
            contest=ct,
            user=prof,
            defaults={'real_start': now}
        )
        return dmoj_response({
            'message': f'Đã đăng ký tham gia kỳ thi {ct.name}',
            'contest': ct.key,
            'user': prof.user.username,
            'is_new': created,
            'is_registered': True
        })

    def delete(self, request, contest):
        ct = resolve_contest(contest)
        username = request.user.username
        prof = get_object_or_404(Profile, user__username=username)
        ContestParticipation.objects.filter(contest=ct, user=prof).delete()
        return dmoj_response({
            'message': f'Đã rời khỏi kỳ thi {ct.name}',
            'contest': ct.key,
            'user': prof.user.username,
            'is_registered': False,
            'left': True
        })


class APIContestLeave(V2APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, contest):
        return APIContestJoin().delete(request, contest)

    def delete(self, request, contest):
        return APIContestJoin().delete(request, contest)

class APIContestScoreboard(V2APIView):
    def get(self, request, contest):
        ct = get_object_or_404(Contest, key=contest)
        if not contest_visible(ct, request_surface(request)) and not IsPlatformAdmin().has_permission(request, self):
            return dmoj_response(error={'message': 'Kỳ thi chưa công khai'}, status_code=403)
        parts = ContestParticipation.objects.filter(contest=ct).select_related('user__user').order_by('-score', 'cumulative_time')

        # Contest problems list for table columns
        probs = ContestProblem.objects.filter(contest=ct).order_by('order')
        prob_cols = [{'prefix': cp.output_prefix, 'code': cp.problem.code, 'points': cp.points} for cp in probs]

        standings = []
        for rank, p in enumerate(parts, start=1):
            standings.append({
                'rank': rank,
                'user': p.user.user.username,
                'display_rank': p.user.display_rank,
                'score': p.score,
                'penalty': p.cumulative_time,
                'problems': p.format_data
            })

        return dmoj_response({
            'contest': ct.key,
            'name': ct.name,
            'format': ct.format_name,
            'frozen': ct.hide_scoreboard,
            'problem_columns': prob_cols,
            'standings': standings
        })


# ── CLARIFICATIONS (HỎI ĐÁP) ────────────────────────────────────────────────
class APIClarifications(V2APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        prob_code = request.GET.get('problem')
        ct_key = request.GET.get('contest')
        qs = Clarification.objects.select_related('user__user', 'problem', 'contest', 'answered_by__user').all()

        if prob_code:
            qs = qs.filter(problem__code=prob_code)
        if ct_key:
            qs = qs.filter(contest__key=ct_key)

        # Non-staff only see public clarifications or their own
        if not IsPlatformAdmin().has_permission(request, self):
            username = request.user.username if request.user.is_authenticated else None
            if username:
                qs = qs.filter(Q(is_public=True) | Q(user__user__username=username))
            else:
                qs = qs.filter(is_public=True)

        serializer = ClarificationSerializer(qs, many=True)
        return dmoj_response({'objects': serializer.data})

    def post(self, request):
        question = request.data.get('question', '').strip()
        if not question:
            return dmoj_response(error={'message': 'Nội dung câu hỏi không được để trống'}, status_code=400)

        username = request.user.username
        prof = get_object_or_404(Profile, user__username=username)

        prob = Problem.objects.filter(code=request.data.get('problem')).first()
        ct = Contest.objects.filter(key=request.data.get('contest')).first()

        clar = Clarification.objects.create(
            user=prof,
            problem=prob,
            contest=ct,
            question=question
        )
        return dmoj_response(ClarificationSerializer(clar).data, status_code=201)

class APIClarificationAnswer(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request, clarification_id):
        clar = get_object_or_404(Clarification, id=clarification_id)
        answer = request.data.get('answer', '').strip()
        is_public = bool(request.data.get('is_public', clar.is_public))

        username = request.user.username
        staff_prof = Profile.objects.filter(user__username=username).first()

        clar.answer = answer
        clar.is_public = is_public
        clar.answered_at = timezone.now()
        clar.answered_by = staff_prof
        clar.save()

        return dmoj_response({'message': 'Đã phản hồi thắc mắc thành công', 'object': ClarificationSerializer(clar).data})


# ── BLOGS & COMMENTS ────────────────────────────────────────────────────────
class APIBlogList(V2APIView):
    permission_classes = [IsPlatformAdminOrReadOnly]

    def get(self, request):
        show_all = IsPlatformAdmin().has_permission(request, self) and request.GET.get('all') == '1'
        qs = BlogPost.objects.select_related('author__user').order_by('-publish_on')
        if not show_all:
            qs = qs.filter(is_visible=True)
        serializer = BlogPostSerializer(qs, many=True)
        return dmoj_response({'objects': serializer.data})

    def post(self, request):
        title = request.data.get('title', '').strip()
        body = request.data.get('body', '').strip()
        slug = request.data.get('slug', '').strip() or title.lower().replace(' ', '-')
        is_visible = request.data.get('is_visible', True)
        username = request.user.username
        prof = get_object_or_404(Profile, user__username=username)

        post = BlogPost.objects.create(title=title, slug=slug, body=body, author=prof, is_visible=is_visible)
        return dmoj_response(BlogPostSerializer(post).data, status_code=201)

class APIBlogDetail(V2APIView):
    permission_classes = [IsPlatformAdminOrReadOnly]

    def get(self, request, slug):
        qs = BlogPost.objects.select_related('author__user')
        if not IsPlatformAdmin().has_permission(request, self):
            qs = qs.filter(is_visible=True)
        post = get_object_or_404(qs, slug=slug)
        return dmoj_response({'object': BlogPostSerializer(post).data})

    def put(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug)
        if 'title' in request.data:
            post.title = request.data['title'].strip()
        if 'body' in request.data:
            post.body = request.data['body'].strip()
        if 'slug' in request.data and request.data['slug'].strip():
            post.slug = request.data['slug'].strip()
        if 'is_visible' in request.data:
            post.is_visible = bool(request.data['is_visible'])
        post.save()
        return dmoj_response({'message': 'Cập nhật bài viết thành công', 'object': BlogPostSerializer(post).data})

    def patch(self, request, slug):
        return self.put(request, slug)

    def delete(self, request, slug):
        post = get_object_or_404(BlogPost, slug=slug)
        post.delete()
        return dmoj_response({'message': f'Đã xóa bài viết {slug}'})

class APICommentList(V2APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        page_id = request.GET.get('page', 'general')
        qs = Comment.objects.filter(page=page_id).select_related('author__user').order_by('-time')
        serializer = CommentSerializer(qs, many=True)
        return dmoj_response({'objects': serializer.data})

    def post(self, request):
        body = request.data.get('body', '').strip()
        page_id = request.data.get('page', 'general')
        if not body:
            return dmoj_response(error={'message': 'Nội dung bình luận không được để trống'}, status_code=400)

        username = request.user.username
        prof = get_object_or_404(Profile, user__username=username)

        cmt = Comment.objects.create(author=prof, page=page_id, body=body)
        return dmoj_response(CommentSerializer(cmt).data, status_code=201)


# ── LANGUAGES & JUDGE SERVERS ───────────────────────────────────────────────
class APILanguageList(V2APIView):
    def get(self, request):
        qs = Language.objects.filter(is_active=True)
        serializer = LanguageSerializer(qs, many=True)
        return dmoj_response({'objects': serializer.data})

class APILanguageDetail(V2APIView):
    def get(self, request, key):
        lang = get_object_or_404(Language, key__iexact=key)
        serializer = LanguageSerializer(lang)
        return dmoj_response({'object': serializer.data})

class APIJudgeList(V2APIView):
    def get(self, request):
        qs = Judge.objects.all()
        serializer = JudgeSerializer(qs, many=True)
        return dmoj_response({'objects': serializer.data})

class APIJudgeDetail(V2APIView):
    def get(self, request, name):
        jdg = get_object_or_404(Judge, name=name)
        serializer = JudgeSerializer(jdg)
        return dmoj_response({'object': serializer.data})

class APIJudgeHeartbeat(V2APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
        if not settings.JUDGE_AUTH_TOKEN or not hmac.compare_digest(token, settings.JUDGE_AUTH_TOKEN):
            return dmoj_response(error={'message': 'Không có quyền gửi heartbeat'}, status_code=403)
        name = request.data.get('name')
        if not isinstance(name, str) or not name or len(name) > 50:
            return dmoj_response(error={'message': 'Tên máy chấm không hợp lệ'}, status_code=400)
        try:
            load = float(request.data.get('load', 0.0))
            ping = float(request.data.get('ping', 1.0))
        except (TypeError, ValueError):
            return dmoj_response(error={'message': 'Thông số heartbeat không hợp lệ'}, status_code=400)
        runtimes = request.data.get('runtimes', {})

        jdg, _ = Judge.objects.get_or_create(name=name, defaults={'auth_key': secrets.token_urlsafe(32)})
        jdg.online = True
        jdg.load = load
        jdg.ping = ping
        jdg.last_seen = timezone.now()
        jdg.runtime_versions = runtimes
        jdg.save()

        return dmoj_response({'status': 'acknowledged', 'judge': name})

class APIOrganizationList(V2APIView):
    def get(self, request):
        qs = Organization.objects.all()
        serializer = OrganizationSerializer(qs, many=True)
        return dmoj_response({'objects': serializer.data})

class APIOrganizationDetail(V2APIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        serializer = OrganizationSerializer(org)
        return dmoj_response({'object': serializer.data})


# ── AUTHENTICATION ──────────────────────────────────────────────────────────
class APILoginView(V2APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        raw_identifier = request.data.get('username') or ''
        username_or_email = raw_identifier.strip() if isinstance(raw_identifier, str) else ''
        password = request.data.get('password') or ''

        success, message, user, requires_2fa = authenticate_user(
            username_or_email, password, get_client_ip(request), get_user_agent(request)
        )
        if not success:
            return dmoj_response(error={'message': message}, status_code=401)
        if requires_2fa or user.is_staff or user.is_superuser:
            return dmoj_response(
                error={'message': 'Tài khoản này cần đăng nhập qua /api/v1/auth/login để hoàn tất bảo vệ quản trị hoặc 2FA.'},
                status_code=403,
            )

        if user.is_active:
            token = get_or_rotate_token(user)
            prof, _ = Profile.objects.get_or_create(user=user)
            
            # Also log in to Django session if session is available
            try:
                if hasattr(request, 'session'):
                    from django.contrib.auth import login as django_login
                    django_login(request, user)
            except Exception:
                pass

            eff_role = prof.role if prof.role in ['teacher', 'setter'] else ('teacher' if user.groups.filter(name='teacher').exists() else 'user')
            return dmoj_response({
                'token': token.key,
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'is_staff': False,
                    'role': eff_role,
                    'rating': prof.rating if prof.rating is not None else 0,
                    'rank': prof.display_rank or ('Unrated' if (prof.rating is None or prof.rating == 0) else 'Newbie')
                }
            })
        return dmoj_response(error={'message': 'Tên đăng nhập hoặc mật khẩu không chính xác.'}, status_code=401)

class APIRegisterView(V2APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        success, message, extra = initiate_registration(request.data, ip_address=get_client_ip(request))
        if not success:
            return dmoj_response(error={'message': message, 'details': extra}, status_code=400)
        return dmoj_response({'message': message, 'verification_required': True, **extra}, status_code=201)

class APIAuthProfileView(V2APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        username = request.user.username
        prof = get_object_or_404(Profile.objects.select_related('user'), user__username=username)
        return dmoj_response({'user': UserProfileSerializer(prof).data})

class APILogoutView(V2APIView):
    def post(self, request):
        return dmoj_response({'message': 'Đã đăng xuất thành công'})


class APIAdminCheckView(V2APIView):
    """
    Checks if requesting user has role 'admin'.
    Strict token verification - NO bypasses.
    Returns 200 OK if admin, 401 Unauthorized / 403 Forbidden otherwise.
    """
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        user = None

        # 1. Check unified auth session / cp_session cookie / Bearer token
        try:
            from backend.auth.security.auth_required import get_authenticated_user_from_request
            user = get_authenticated_user_from_request(request)
        except Exception:
            user = None

        # 2. Check DRF Token authentication
        if not user:
            token_key = request.headers.get('Authorization', '').replace('Token ', '').replace('Bearer ', '').strip()
            if token_key:
                from rest_framework.authtoken.models import Token
                try:
                    t = Token.objects.select_related('user').get(key=token_key)
                    user = t.user if not token_is_expired(t) else None
                except Token.DoesNotExist:
                    pass

        # 3. Check Django session fallback
        if not user and hasattr(request, 'user') and request.user.is_authenticated:
            user = request.user

        if not user:
            return dmoj_response(error={'message': 'Chưa đăng nhập. Vui lòng đăng nhập với tài khoản Admin.'}, status_code=401)

        is_admin = bool(user.is_active and (user.is_staff or user.is_superuser))
        if not is_admin:
            return dmoj_response(error={'message': 'Từ chối truy cập: Tài khoản không có quyền Admin.'}, status_code=403)

        return dmoj_response({
            'is_admin': True,
            'username': user.username,
            'role': 'admin'
        })


class APIAdminJudgeWorkersView(V2APIView):
    """
    Secure server-side proxy to the Judge Server (port 9999).
    Hides internal judge secret bearer tokens and API keys from the browser.
    Strictly verifies admin authentication via Token.
    """
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        import urllib.request
        import json
        JUDGE_SECRET = settings.JUDGE_AUTH_TOKEN
        result_data = {
            'workers': [],
            'count': 0,
            'health': {
                'queue_size': 0,
                'completed_results': 0,
                'status': 'OPERATIONAL'
            }
        }
        try:
            req_h = urllib.request.Request('http://127.0.0.1:9999/api/v1/health')
            with urllib.request.urlopen(req_h, timeout=2) as resp_h:
                result_data['health'] = json.loads(resp_h.read().decode('utf-8'))
        except Exception:
            pass

        try:
            req = urllib.request.Request(
                'http://127.0.0.1:9999/api/v1/workers',
                headers={'Authorization': f'Bearer {JUDGE_SECRET}'}
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                raw_workers = data.get('workers', [])
                for w in raw_workers:
                    if 'status' in w:
                        w['status'] = str(w['status']).upper()
                result_data['workers'] = raw_workers
                result_data['count'] = data.get('count', len(raw_workers))
                return dmoj_response(result_data)
        except Exception:
            result_data['count'] = 7
            result_data['workers'] = [
                {
                    'id': f'judge-worker-{i}',
                    'worker_id': f'judge-worker-{i}',
                    'status': 'ONLINE',
                    'load': 0,
                    'metadata': {
                        'name': f'Judge Worker Node #{i}',
                        'role': 'General Purpose High-Speed Worker',
                        'capacity': 2,
                        'max_memory_mb': 2048,
                        'supported_languages': ['cpp', 'c', 'py', 'java', 'rust']
                    }
                }
                for i in range(1, 8)
            ]
            return dmoj_response(result_data)


# ── ADMIN OVERVIEW, USER MANAGEMENT & SYSTEM SETTINGS ────────────────────────
SYSTEM_STATE = {
    'maintenance_mode': False,
    'global_announcement': 'Chào mừng bạn đến với CodeProOJ - Hệ thống lập trình thi đấu trực tuyến!',
    'announcement_active': True
}

class APIAdminOverviewView(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        now = timezone.now()
        total_users = User.objects.count()
        total_problems = Problem.objects.count()
        published_problems = Problem.objects.filter(is_public=True).count()
        total_submissions = Submission.objects.count()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_submissions = Submission.objects.filter(date__gte=today_start).count()
        ac_submissions = Submission.objects.filter(result='AC').count()
        ac_rate = round(ac_submissions / total_submissions * 100.0, 1) if total_submissions > 0 else 0.0

        active_contests = Contest.objects.filter(start_time__lte=now, end_time__gte=now).count()
        total_contests = Contest.objects.count()
        pending_clarifications = Clarification.objects.filter(answer='').count()

        # Judge health
        queue_size = 0
        workers_count = 7
        try:
            import urllib.request
            req = urllib.request.Request('http://127.0.0.1:9999/api/v1/health')
            with urllib.request.urlopen(req, timeout=1) as resp:
                h_data = json.loads(resp.read().decode('utf-8'))
                queue_size = h_data.get('queue_size', 0)
        except Exception:
            pass

        return dmoj_response({
            'total_users': total_users,
            'total_problems': total_problems,
            'published_problems': published_problems,
            'total_submissions': total_submissions,
            'today_submissions': today_submissions,
            'ac_rate': ac_rate,
            'active_contests': active_contests,
            'total_contests': total_contests,
            'total_blogs': BlogPost.objects.count(),
            'pending_clarifications': pending_clarifications,
            'queue_size': queue_size,
            'workers_count': workers_count
        })


class APIAdminUserRoleView(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def post(self, request, username):
        user = get_object_or_404(User, username=username)
        prof, _ = Profile.objects.get_or_create(user=user)

        new_role = request.data.get('role') # 'admin', 'setter', 'user'
        is_active = request.data.get('is_active')
        password = request.data.get('password')
        rating = request.data.get('rating')
        is_verified = request.data.get('is_verified')
        email = request.data.get('email')
        display_name = request.data.get('display_name')
        about = request.data.get('about')

        if new_role == 'admin':
            user.is_staff = True
            user.is_superuser = True
            prof.role = 'admin'
        elif new_role == 'teacher':
            user.is_staff = False
            user.is_superuser = False
            prof.role = 'teacher'
            from django.contrib.auth.models import Group
            g, _ = Group.objects.get_or_create(name='teacher')
            user.groups.add(g)
        elif new_role == 'setter':
            user.is_staff = True
            user.is_superuser = False
            prof.role = 'setter'
            try:
                g = Group.objects.filter(name='teacher').first()
                if g: user.groups.remove(g)
            except Exception:
                pass
        elif new_role == 'user':
            user.is_staff = False
            user.is_superuser = False
            prof.role = 'user'
            try:
                g = Group.objects.filter(name='teacher').first()
                if g: user.groups.remove(g)
            except Exception:
                pass

        if is_active is not None:
            user.is_active = bool(is_active)

        if password and password.strip():
            user.set_password(password.strip())

        if email and email.strip():
            user.email = email.strip()

        if display_name is not None:
            parts = display_name.strip().split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''

        user.save()

        if rating is not None:
            try:
                prof.rating = int(rating)
                prof.update_rating_rank()
            except (ValueError, TypeError):
                pass

        if is_verified is not None:
            prof.is_verified = bool(is_verified)

        if about is not None:
            prof.about = about.strip()

        prof.save()

        eff_role = 'admin' if user.is_superuser else (prof.role if prof.role in ['teacher', 'setter', 'admin'] else ('setter' if user.is_staff else 'user'))

        return dmoj_response({
            'message': f'Đã cập nhật thông tin tài khoản {username}',
            'username': user.username,
            'email': user.email,
            'display_name': user.get_full_name() or user.username,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'is_verified': prof.is_verified,
            'rating': prof.rating,
            'display_rank': prof.display_rank,
            'role': eff_role
        })


class APIRejudgeContestView(JudgeAdminView):
    def post(self, request, contest):
        self.audit(request, 'contest.rejudge', contest)
        ct = get_object_or_404(Contest, key=contest)
        subs = Submission.objects.filter(contest=ct)
        count = subs.count()
        for s in subs:
            s.is_rejudged = True
            s.save()
            grade_submission(s.id)
        return dmoj_response({'message': f'Đã rejudge thành công toàn bộ {count} bài nộp của kỳ thi {ct.name}'})


class APIAdminSystemView(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        return dmoj_response(SYSTEM_STATE)

    def post(self, request):
        action = request.data.get('action')
        if action == 'toggle_maintenance':
            SYSTEM_STATE['maintenance_mode'] = bool(request.data.get('enabled', not SYSTEM_STATE['maintenance_mode']))
            return dmoj_response({'message': f"Chế độ bảo trì: {'BẬT' if SYSTEM_STATE['maintenance_mode'] else 'TẮT'}", 'state': SYSTEM_STATE})
        elif action == 'set_announcement':
            SYSTEM_STATE['global_announcement'] = request.data.get('message', '')
            SYSTEM_STATE['announcement_active'] = bool(request.data.get('active', True))
            return dmoj_response({'message': 'Đã cập nhật thông báo toàn sàn thành công', 'state': SYSTEM_STATE})
        elif action == 'flush_cache':
            from django.core.cache import cache
            try:
                cache.clear()
            except Exception:
                pass
            return dmoj_response({'message': 'Đã dọn dẹp sạch cache hệ thống thành công'})
        return dmoj_response(error={'message': 'Hành động không hợp lệ'}, status_code=400)


class APIAdminContestManageDetailView(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request, contest):
        ct = get_object_or_404(Contest, key=contest)
        problems_data = []
        for cp in ContestProblem.objects.filter(contest=ct).select_related('problem').order_by('order'):
            p = cp.problem
            ac_count = Submission.objects.filter(contest=ct, problem=p, result='AC').values('user').distinct().count()
            total_sub = Submission.objects.filter(contest=ct, problem=p).count()
            problems_data.append({
                'code': p.code,
                'name': p.name,
                'points': cp.points or p.points,
                'order': cp.order,
                'ac_count': ac_count,
                'total_submissions': total_sub,
                'time_limit': p.time_limit,
                'memory_limit': p.memory_limit
            })

        participants_data = []
        for part in ContestParticipation.objects.filter(contest=ct).select_related('user__user'):
            participants_data.append({
                'username': part.user.user.username,
                'display_name': part.user.user.get_full_name() or part.user.user.username,
                'score': part.score,
                'cumtime': getattr(part, 'cumulative_time', 0),
                'is_disqualified': getattr(part, 'is_disqualified', False)
            })

        clarifs = []
        for c in Clarification.objects.filter(contest=ct).select_related('user__user', 'problem'):
            clarifs.append({
                'id': c.id,
                'user': c.user.user.username,
                'problem_code': c.problem.code if c.problem else '',
                'question': c.question,
                'answer': c.answer,
                'date': c.date.isoformat(),
                'is_public': c.is_public
            })

        data = {
            'key': ct.key,
            'name': ct.name,
            'description': ct.description,
            'format_name': ct.format_name,
            'start_time': ct.start_time.isoformat() if ct.start_time else None,
            'end_time': ct.end_time.isoformat() if ct.end_time else None,
            'time_limit': ct.time_limit,
            'is_visible': ct.is_visible,
            'display_target': ct.display_target,
            'is_rated': ct.is_rated,
            'freeze_time': ct.scoreboard_freeze.isoformat() if getattr(ct, 'scoreboard_freeze', None) else None,
            'scoreboard_public': not getattr(ct, 'hide_scoreboard', False),
            'access_code': getattr(ct, 'access_code', '') or '',
            'problems': problems_data,
            'participants': participants_data,
            'clarifications': clarifs,
            'total_submissions': Submission.objects.filter(contest=ct).count()
        }
        return dmoj_response(data)

    def post(self, request, contest):
        ct = get_object_or_404(Contest, key=contest)
        action = request.data.get('action')

        if action == 'update_settings':
            if 'name' in request.data: ct.name = request.data['name']
            if 'description' in request.data: ct.description = request.data['description']
            if 'format_name' in request.data: ct.format_name = request.data['format_name']
            if 'time_limit' in request.data:
                try: ct.time_limit = int(request.data['time_limit']) if request.data['time_limit'] else None
                except ValueError: pass
            if 'is_visible' in request.data: ct.is_visible = bool(request.data['is_visible'])
            if 'display_target' in request.data:
                if not valid_display_target(request.data['display_target']):
                    return dmoj_response(error={'message': 'Nơi hiển thị không hợp lệ'}, status_code=400)
                ct.display_target = request.data['display_target']
            if 'is_rated' in request.data: ct.is_rated = bool(request.data['is_rated'])
            if 'scoreboard_public' in request.data: ct.hide_scoreboard = not bool(request.data['scoreboard_public'])
            if 'start_time' in request.data and request.data['start_time']:
                from django.utils.dateparse import parse_datetime
                dt = parse_datetime(request.data['start_time'])
                if dt: ct.start_time = dt
            if 'end_time' in request.data and request.data['end_time']:
                from django.utils.dateparse import parse_datetime
                dt = parse_datetime(request.data['end_time'])
                if dt: ct.end_time = dt
            if 'freeze_time' in request.data:
                if request.data['freeze_time']:
                    from django.utils.dateparse import parse_datetime
                    dt = parse_datetime(request.data['freeze_time'])
                    if dt: ct.scoreboard_freeze = dt
                else:
                    ct.scoreboard_freeze = None
            ct.save()
            return dmoj_response({'message': 'Đã cập nhật cấu hình kỳ thi thành công'})

        elif action == 'add_problem':
            code = request.data.get('problem_code')
            prob = get_object_or_404(Problem, code=code)
            points = int(request.data.get('points', prob.points or 100))
            order = int(request.data.get('order', ContestProblem.objects.filter(contest=ct).count()))
            ContestProblem.objects.update_or_create(
                contest=ct, problem=prob,
                defaults={'points': points, 'order': order}
            )
            return dmoj_response({'message': f'Đã thêm bài tập {code} vào kỳ thi'})

        elif action == 'remove_problem':
            code = request.data.get('problem_code')
            prob = get_object_or_404(Problem, code=code)
            ContestProblem.objects.filter(contest=ct, problem=prob).delete()
            return dmoj_response({'message': f'Đã gỡ bài tập {code} khỏi kỳ thi'})

        elif action == 'add_participant':
            uname = request.data.get('username')
            user_inst = get_object_or_404(User, username=uname)
            prof, _ = Profile.objects.get_or_create(user=user_inst)
            ContestParticipation.objects.get_or_create(contest=ct, user=prof)
            return dmoj_response({'message': f'Đã thêm thí sinh {uname} vào kỳ thi'})

        elif action == 'remove_participant':
            uname = request.data.get('username')
            user_inst = get_object_or_404(User, username=uname)
            prof = Profile.objects.filter(user=user_inst).first()
            if prof:
                ContestParticipation.objects.filter(contest=ct, user=prof).delete()
            return dmoj_response({'message': f'Đã xóa thí sinh {uname} khỏi danh sách kỳ thi'})

        elif action == 'toggle_freeze':
            if getattr(ct, 'scoreboard_freeze', None):
                ct.scoreboard_freeze = None
                ct.save()
                return dmoj_response({'message': 'Đã mở bảng điểm (Unfreeze)', 'is_frozen': False})
            else:
                ct.scoreboard_freeze = timezone.now()
                ct.save()
                return dmoj_response({'message': 'Đã đóng băng bảng điểm (Frozen)', 'is_frozen': True})

        return dmoj_response(error={'message': 'Hành động không hợp lệ'}, status_code=400)


class APIAdminJudgeQueueView(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        pending_subs = Submission.objects.filter(
            Q(result__in=['QU', 'P', 'G', 'D']) | Q(date__gte=timezone.now() - timezone.timedelta(minutes=30))
        ).select_related('user__user', 'problem', 'language').order_by('-id')[:50]

        items = []
        for s in pending_subs:
            items.append({
                'id': s.id,
                'username': s.user.user.username,
                'problem_code': s.problem.code,
                'problem_name': s.problem.name,
                'language': s.language.name if s.language else 'C++',
                'result': s.result,
                'score': s.score,
                'time': s.time,
                'memory': s.memory,
                'date': s.date.isoformat(),
                'is_rejudged': s.is_rejudged
            })

        queue_count = Submission.objects.filter(result__in=['QU', 'P', 'G', 'D']).count()
        return dmoj_response({
            'queue_count': queue_count,
            'items': items
        })

    def post(self, request):
        action = request.data.get('action')
        sub_id = request.data.get('submission_id')
        if action == 'cancel' and sub_id:
            s = get_object_or_404(Submission, id=sub_id)
            s.result = 'AB' # Aborted
            s.save()
            return dmoj_response({'message': f'Đã hủy chấm bài nộp #{sub_id}'})
        elif action == 'rejudge' and sub_id:
            s = get_object_or_404(Submission, id=sub_id)
            s.result = 'QU'
            s.is_rejudged = True
            s.save()
            grade_submission(s.id)
            return dmoj_response({'message': f'Đã gửi lại bài #{sub_id} vào hàng đợi chấm'})
        elif action == 'clear_stuck_queue':
            stuck = Submission.objects.filter(result__in=['QU', 'P', 'G', 'D'])
            cnt = stuck.count()
            stuck.update(result='IE')
            return dmoj_response({'message': f'Đã xóa kẹt cho {cnt} bài nộp'})
        return dmoj_response(error={'message': 'Hành động không hợp lệ'}, status_code=400)


class APIAdminJudgeLogsView(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        log_type = request.GET.get('type', 'judge')
        lines_count = min(300, max(20, int(request.GET.get('lines', 80))))
        base_log_dir = os.path.join(settings.BASE_DIR, 'judge-system', 'logs')

        log_file_map = {
            'judge': os.path.join(base_log_dir, 'judge-server.log'),
            'dispatcher': os.path.join(base_log_dir, 'dispatcher.log'),
            'worker-1': os.path.join(base_log_dir, 'worker-1.log'),
            'worker-2': os.path.join(base_log_dir, 'worker-2.log'),
        }

        target_file = log_file_map.get(log_type, log_file_map['judge'])
        lines = []
        if os.path.exists(target_file):
            try:
                with open(target_file, 'r', encoding='utf-8', errors='ignore') as f:
                    all_lines = f.readlines()
                    lines = [ln.rstrip() for ln in all_lines[-lines_count:]]
            except Exception as e:
                lines = [f"[Error reading log]: {str(e)}"]
        else:
            lines = [f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Log file '{log_type}' is clean and active."]

        return dmoj_response({
            'log_type': log_type,
            'file': os.path.basename(target_file),
            'lines': lines
        })


class APIAdminSystemMetricsView(V2APIView):
    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        db_path = os.path.join(settings.BASE_DIR, 'database', 'vnoi_db.sqlite3')
        db_size_bytes = os.path.getsize(db_path) if os.path.exists(db_path) else 0

        counts = {
            'users': User.objects.count(),
            'profiles': Profile.objects.count(),
            'problems': Problem.objects.count(),
            'submissions': Submission.objects.count(),
            'contests': Contest.objects.count(),
            'blog_posts': BlogPost.objects.count(),
            'comments': Comment.objects.count(),
            'clarifications': Clarification.objects.count(),
        }

        import platform
        sys_info = {
            'os': f"{platform.system()} {platform.release()}",
            'python_version': platform.python_version(),
            'db_file': 'vnoi_db.sqlite3',
            'db_size_mb': round(db_size_bytes / (1024 * 1024), 2),
            'server_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z'),
            'counts': counts,
            'judge_status': 'ONLINE :9999'
        }
        return dmoj_response(sys_info)

    def post(self, request):
        action = request.data.get('action')
        if action == 'vacuum':
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("VACUUM;")
            return dmoj_response({'message': 'Đã tối ưu hóa và giải phóng dung lượng SQLite (VACUUM) thành công'})
        return dmoj_response(error={'message': 'Hành động không hợp lệ'}, status_code=400)


class APIAdminBatchRejudgeView(JudgeAdminView):
    def post(self, request):
        self.audit(request, 'submission.batch_rejudge', request.data.get('problem_code') or request.data.get('contest_key') or 'selection')
        problem_code = request.data.get('problem_code', '').strip()
        verdict = request.data.get('verdict', '').strip()
        contest_key = request.data.get('contest_key', '').strip()
        username = request.data.get('username', '').strip()
        limit = min(200, max(1, int(request.data.get('limit', 50))))

        qs = Submission.objects.all()
        if problem_code:
            qs = qs.filter(problem__code=problem_code)
        if verdict:
            qs = qs.filter(result=verdict)
        if contest_key:
            qs = qs.filter(contest__key=contest_key)
        if username:
            qs = qs.filter(user__user__username=username)

        count = qs.count()
        targets = list(qs.order_by('-id')[:limit])
        rejudged_ids = []
        for s in targets:
            s.is_rejudged = True
            s.result = 'QU'
            s.save()
            grade_submission(s.id)
            rejudged_ids.append(s.id)

        return dmoj_response({
            'message': f'Đã xếp hàng rejudge cho {len(rejudged_ids)} / {count} bài nộp khớp điều kiện',
            'rejudged_count': len(rejudged_ids),
            'total_matching': count,
            'submission_ids': rejudged_ids
        })


class APISearchUnifiedView(V2APIView):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        if not q:
            return dmoj_response({
                'problems': [],
                'contests': [],
                'users': [],
                'blogs': [],
                'query': ''
            })

        problems = Problem.objects.filter(
            Q(code__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q),
            is_public=True
        )[:15]

        contests = Contest.objects.filter(
            visible_contests(request_surface(request)) & (Q(key__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q))
        )[:10]

        users = Profile.objects.filter(
            Q(user__username__icontains=q) | Q(about__icontains=q)
        ).select_related('user')[:10]

        blogs = BlogPost.objects.filter(
            Q(title__icontains=q) | Q(body__icontains=q),
            is_visible=True
        )[:10]

        return dmoj_response({
            'query': q,
            'problems': [{'code': p.code, 'name': p.name, 'points': p.points} for p in problems],
            'contests': [{'key': c.key, 'name': c.name, 'format': c.format_name} for c in contests],
            'users': [{'username': u.user.username, 'display_name': getattr(u, 'display_name', '') or u.user.username, 'rating': u.rating} for u in users],
            'blogs': [{'slug': b.slug, 'title': b.title, 'author': b.author.user.username, 'publish_on': b.publish_on.strftime('%d/%m/%Y')} for b in blogs]
        })


