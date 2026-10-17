import json
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q

from backend.judge.models import Organization, Contest, Problem, Profile, Submission
from backend.judge.permissions.authentication import BearerTokenAuthentication, JudgeCookieAuthentication
from .models import (
    OrganizationRole, OrganizationPermission, OrganizationMember,
    OrganizationContest, OrganizationProblem, OrganizationPost,
    OrganizationAnnouncement, OrganizationActivity, OrganizationAuditLog,
    OrganizationInvitation
)
from .serializers import (
    OrganizationDetailSerializer, OrganizationRoleSerializer,
    OrganizationMemberSerializer, OrganizationPostSerializer,
    OrganizationAnnouncementSerializer, OrganizationActivitySerializer,
    OrganizationAuditLogSerializer, OrganizationInvitationSerializer
)
from .permissions import user_has_org_permission, get_user_org_role


class OrganizationAPIView(APIView):
    authentication_classes = [TokenAuthentication, BearerTokenAuthentication, JudgeCookieAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

def resolve_user(request):
    """Resolve the active account authenticated by DRF."""
    if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_active:
        return request.user
    return None

def log_audit(org, actor, action, target, ip='127.0.0.1', details=''):
    try:
        OrganizationAuditLog.objects.create(
            organization=org, actor=actor, action=action, target=target, ip=ip, details=details
        )
    except Exception:
        pass

def log_activity(org, user, action, target_type='', target_id='', target_title=''):
    try:
        OrganizationActivity.objects.create(
            organization=org, user=user, action=action,
            target_type=target_type, target_id=target_id, target_title=target_title
        )
    except Exception:
        pass

# ── 1. ORGANIZATIONS ROOT LIST & CREATE ────────────────────────────────────────
class OrganizationListCreateAPIView(OrganizationAPIView):
    def get(self, request):
        search = request.GET.get('search', '').strip()
        qs = Organization.objects.all().order_by('-member_count', 'name')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(slug__icontains=search) | Q(short_name__icontains=search))
        
        serializer = OrganizationDetailSerializer(qs, many=True, context={'request': request})
        return Response({'status': 200, 'data': serializer.data})

    def post(self, request):
        user = resolve_user(request)
        if not user:
            return Response({'status': 401, 'error': 'Vui lòng đăng nhập để tạo tổ chức.'}, status=401)
        
        prof = getattr(user, 'profile', None)
        if not prof:
            prof, _ = Profile.objects.get_or_create(user=user)

        if not prof.can_create_organization():
            return Response({'status': 403, 'error': 'Chỉ Quản trị viên (Admin) và Giáo viên (Teacher) mới có quyền tạo tổ chức.'}, status=403)
        
        data = request.data
        slug = data.get('slug', '').strip().lower()
        name = data.get('name', '').strip()
        short_name = data.get('short_name', '').strip() or name[:10]
        
        if not slug or not name:
            return Response({'status': 400, 'error': 'Tên và Slug tổ chức là bắt buộc.'}, status=400)
        
        if Organization.objects.filter(slug=slug).exists():
            return Response({'status': 400, 'error': f'Tổ chức có mã slug "{slug}" đã tồn tại.'}, status=400)

        org = Organization.objects.create(
            name=name,
            slug=slug,
            short_name=short_name,
            about=data.get('about', ''),
            description=data.get('description', ''),
            website=data.get('website', ''),
            logo=data.get('logo', '/frontend/assets/icons/org-default.svg'),
            cover=data.get('cover', ''),
            is_open=data.get('is_open', True),
            owner_id=user.id,
            verified=bool(data.get('verified', False)) if (user.is_staff or user.is_superuser) else False
        )

        # Create default roles
        owner_role = OrganizationRole.objects.create(organization=org, name='Owner', color='#ef4444', is_default=False)
        OrganizationPermission.objects.create(role=owner_role, permission='*')
        
        admin_role = OrganizationRole.objects.create(organization=org, name='Administrator', color='#8b5cf6', is_default=False)
        for p in ['organization.edit', 'member.manage', 'contest.*', 'problem.*', 'blog.*', 'announcement.create']:
            OrganizationPermission.objects.create(role=admin_role, permission=p)

        member_role = OrganizationRole.objects.create(organization=org, name='Member', color='#64748b', is_default=True)
        OrganizationPermission.objects.create(role=member_role, permission='organization.view')

        # Add creator as Owner
        OrganizationMember.objects.create(organization=org, user=user, role=owner_role, status='active')

        log_audit(org, user, 'CREATE_ORGANIZATION', org.name, details='Khởi tạo tổ chức mới')
        log_activity(org, user, 'create_organization', 'organization', org.slug, org.name)

        serializer = OrganizationDetailSerializer(org, context={'request': request})
        return Response({'status': 201, 'message': 'Tạo tổ chức thành công', 'data': serializer.data}, status=201)

# ── 2. ORGANIZATION DETAIL & UPDATE ──────────────────────────────────────────
class OrganizationDetailAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        serializer = OrganizationDetailSerializer(org, context={'request': request})
        return Response({'status': 200, 'data': serializer.data})

    def patch(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        user = resolve_user(request)
        if not user_has_org_permission(user, org, 'organization.edit'):
            return Response({'status': 403, 'error': 'Bạn không có quyền chỉnh sửa thông tin tổ chức này.'}, status=403)

        data = request.data
        for f in ['name', 'short_name', 'about', 'description', 'website', 'logo', 'cover', 'is_open']:
            if f in data:
                setattr(org, f, data[f])
        if 'verified' in data and (user.is_superuser or user.is_staff):
            org.verified = bool(data['verified'])
        org.save()

        log_audit(org, user, 'UPDATE_SETTINGS', 'Organization Profile', details=f"Cập nhật cài đặt tổ chức {org.slug}")
        serializer = OrganizationDetailSerializer(org, context={'request': request})
        return Response({'status': 200, 'message': 'Cập nhật thông tin thành công', 'data': serializer.data})

    def delete(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        user = resolve_user(request)
        if not user or not (user.is_superuser or user.is_staff):
            return Response({'status': 403, 'error': 'Chỉ Quản trị viên hệ thống mới có quyền xóa tổ chức.'}, status=403)
        org_name = org.name
        org.delete()
        return Response({'status': 200, 'message': f'Đã xóa tổ chức "{org_name}" thành công!'})

# ── 3. JOIN & LEAVE ORGANIZATION ─────────────────────────────────────────────
class OrganizationJoinAPIView(OrganizationAPIView):
    def post(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        user = resolve_user(request)
        if not user:
            return Response({'status': 401, 'error': 'Vui lòng đăng nhập để tham gia tổ chức.'}, status=401)

        mem = OrganizationMember.objects.filter(organization=org, user=user).first()
        if mem:
            if mem.status == 'banned':
                return Response({'status': 403, 'error': 'Tài khoản của bạn đã bị cấm khỏi tổ chức này.'}, status=403)
            return Response({'status': 200, 'message': 'Bạn đã là thành viên của tổ chức này.'})

        default_role = OrganizationRole.objects.filter(organization=org, is_default=True).first()
        if not default_role:
            default_role = OrganizationRole.objects.filter(organization=org, name='Member').first()
        if not default_role:
            default_role = OrganizationRole.objects.create(organization=org, name='Member', color='#64748b', is_default=True)

        status_val = 'active' if org.is_open else 'pending'
        OrganizationMember.objects.create(organization=org, user=user, role=default_role, status=status_val)

        org.member_count = org.org_members.filter(status='active').count()
        org.save(update_fields=['member_count'])

        log_activity(org, user, 'join_organization', 'user', user.username, f"{user.username} đã tham gia {org.short_name or org.name}")
        msg = 'Tham gia tổ chức thành công!' if status_val == 'active' else 'Yêu cầu tham gia đã gửi, vui lòng chờ duyệt.'
        return Response({'status': 200, 'message': msg, 'membership_status': status_val})

class OrganizationLeaveAPIView(OrganizationAPIView):
    def post(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        user = resolve_user(request)
        if not user:
            return Response({'status': 401, 'error': 'Vui lòng đăng nhập.'}, status=401)

        mem = OrganizationMember.objects.filter(organization=org, user=user).first()
        if not mem:
            return Response({'status': 400, 'error': 'Bạn không thuộc tổ chức này.'}, status=400)
        if mem.role.name.lower() == 'owner':
            return Response({'status': 400, 'error': 'Chủ sở hữu (Owner) không thể rời tổ chức. Vui lòng chuyển giao quyền trước.'}, status=400)

        mem.delete()
        org.member_count = org.org_members.filter(status='active').count()
        org.save(update_fields=['member_count'])

        log_activity(org, user, 'leave_organization', 'user', user.username, f"{user.username} đã rời khỏi tổ chức")
        return Response({'status': 200, 'message': 'Đã rời khỏi tổ chức thành công.'})

# ── 4. MEMBERS LIST & MANAGEMENT ─────────────────────────────────────────────
class OrganizationMembersAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        search = request.GET.get('search', '').strip()
        role_filter = request.GET.get('role', '').strip()

        members = OrganizationMember.objects.filter(organization=org, status='active').select_related('user', 'role', 'user__profile')
        if search:
            members = members.filter(Q(user__username__icontains=search) | Q(user__first_name__icontains=search) | Q(user__last_name__icontains=search))
        if role_filter and role_filter != 'all':
            members = members.filter(role__name__iexact=role_filter)

        members = members.order_by('-user__profile__rating', 'user__username')
        serializer = OrganizationMemberSerializer(members, many=True)
        return Response({'status': 200, 'data': serializer.data, 'total': members.count()})

    def post(self, request, slug):
        """Add / invite member directly (requires member.add or member.manage)."""
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'member.add'):
            return Response({'status': 403, 'error': 'Không có quyền thêm thành viên.'}, status=403)

        username = request.data.get('username', '').strip()
        role_name = request.data.get('role', 'Member')
        target_user = User.objects.filter(username=username).first()
        if not target_user:
            return Response({'status': 404, 'error': f'Không tìm thấy người dùng "{username}".'}, status=404)

        role = OrganizationRole.objects.filter(organization=org, name=role_name).first()
        if not role:
            role = OrganizationRole.objects.filter(organization=org, is_default=True).first()

        mem, created = OrganizationMember.objects.get_or_create(
            organization=org, user=target_user,
            defaults={'role': role, 'status': 'active'}
        )
        if not created:
            mem.role = role
            mem.status = 'active'
            mem.save()

        org.member_count = org.org_members.filter(status='active').count()
        org.save(update_fields=['member_count'])

        log_audit(org, actor, 'ADD_MEMBER', target_user.username, details=f"Gán vai trò {role.name}")
        log_activity(org, actor, 'add_member', 'user', target_user.username, f"Thêm {target_user.username} vào tổ chức ({role.name})")

        return Response({'status': 200, 'message': f'Đã thêm thành viên {username} thành công!'})

class OrganizationMemberDetailAPIView(OrganizationAPIView):
    def patch(self, request, slug, username):
        """Change member role or ban/unban status."""
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'member.manage'):
            return Response({'status': 403, 'error': 'Không có quyền quản lý thành viên.'}, status=403)

        target_user = get_object_or_404(User, username=username)
        mem = get_object_or_404(OrganizationMember, organization=org, user=target_user)

        data = request.data
        if 'role' in data:
            new_role = OrganizationRole.objects.filter(organization=org, name=data['role']).first()
            if not new_role:
                new_role = OrganizationRole.objects.filter(organization=org, id=data['role']).first()
            if new_role:
                mem.role = new_role
        if 'status' in data:
            mem.status = data['status']
        mem.save()

        log_audit(org, actor, 'UPDATE_MEMBER', username, details=f"Cập nhật vai trò/trạng thái sang {mem.role.name} / {mem.status}")
        return Response({'status': 200, 'message': f'Cập nhật thành viên {username} thành công!'})

    def delete(self, request, slug, username):
        """Remove member from organization."""
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'member.remove'):
            return Response({'status': 403, 'error': 'Không có quyền xóa thành viên.'}, status=403)

        target_user = get_object_or_404(User, username=username)
        mem = get_object_or_404(OrganizationMember, organization=org, user=target_user)
        if mem.role.name.lower() == 'owner':
            return Response({'status': 400, 'error': 'Không thể xóa Chủ sở hữu (Owner) của tổ chức.'}, status=400)

        mem.delete()
        org.member_count = org.org_members.filter(status='active').count()
        org.save(update_fields=['member_count'])

        log_audit(org, actor, 'REMOVE_MEMBER', username, details="Xóa thành viên khỏi tổ chức")
        return Response({'status': 200, 'message': f'Đã xóa {username} khỏi tổ chức.'})

# ── 5. CONTESTS ──────────────────────────────────────────────────────────────
class OrganizationContestsAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        user = resolve_user(request)

        # Check if caller wants list of available contests to link (for Admin)
        if request.GET.get('available') == '1':
            actor = resolve_user(request)
            if not user_has_org_permission(actor, org, 'contest.create'):
                return Response({'status': 403, 'error': 'Không có quyền quản lý cuộc thi.'}, status=403)
            linked_ids = OrganizationContest.objects.filter(organization=org).values_list('contest_id', flat=True)
            available = Contest.objects.exclude(id__in=linked_ids).order_by('-start_time')[:30]
            data = [{'id': c.id, 'key': c.key, 'name': c.name, 'format': c.format_name} for c in available]
            return Response({'status': 200, 'data': data})

        # Determine caller membership status in this organization
        is_member = False
        is_admin = False
        member_role = None
        if user:
            is_admin = user.is_active and (user.is_staff or user.is_superuser)
            mem = OrganizationMember.objects.filter(organization=org, user=user, status='active').select_related('role').first()
            if mem:
                is_member = True
                member_role = mem.role.name
            elif is_admin:
                is_member = True
                member_role = 'Administrator'

        org_contests = OrganizationContest.objects.filter(
            organization=org,
            contest__is_visible=True,
            contest__display_target__in=['both', 'web'],
        ).select_related('contest')
        total_org_contests = org_contests.count()

        # Cuộc thi tổ chức chỉ hiển thị khi bạn là member trong tổ chức
        if not is_member:
            return Response({
                'status': 200,
                'is_member': False,
                'requires_membership': True,
                'organization_slug': org.slug,
                'organization_name': org.short_name or org.name,
                'total_contests': total_org_contests,
                'message': f'Các cuộc thi của {org.short_name or org.name} là cuộc thi nội bộ chỉ dành riêng cho thành viên. Vui lòng tham gia tổ chức để xem và tham gia thi đấu.',
                'data': []
            })

        now = timezone.now()
        results = []
        for oc in org_contests:
            c = oc.contest
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
                'format': c.format_name,
                'is_rated': c.is_rated,
                'is_official': oc.is_official,
                'is_members_only': True,
                'start_time': c.start_time.isoformat(),
                'end_time': c.end_time.isoformat(),
                'duration_minutes': int(c.time_limit / 60) if c.time_limit else 180,
                'status': c_status,
                'problems_count': c.contest_problems.count(),
                'participants_count': c.participants.count()
            })

        return Response({
            'status': 200,
            'is_member': True,
            'member_role': member_role,
            'requires_membership': False,
            'total_contests': len(results),
            'data': results
        })

    def post(self, request, slug):
        """Link an existing contest to this organization or create a new one."""
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'contest.create'):
            return Response({'status': 403, 'error': 'Không có quyền liên kết cuộc thi.'}, status=403)

        contest_key = request.data.get('contest_key') or request.data.get('contest_id')
        contest_name = request.data.get('contest_name')

        # If user wants to create a new contest directly for this organization
        if not contest_key and contest_name:
            import re, time
            base_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', contest_name.lower())[:25].strip('_')
            slug_key = f"{base_slug}_{int(time.time())}"
            while Contest.objects.filter(key=slug_key).exists():
                slug_key = f"{base_slug}_{int(time.time())}_{Contest.objects.count() + 1}"
            start = timezone.now()
            end = start + timezone.timedelta(hours=3)
            contest = Contest.objects.create(
                key=slug_key,
                name=contest_name,
                description=request.data.get('description', f'Cuộc thi nội bộ của {org.short_name or org.name}'),
                format_name=request.data.get('format', 'icpc'),
                start_time=start,
                end_time=end,
                time_limit=10800,
                is_rated=request.data.get('is_rated', False),
                is_visible=True
            )
        else:
            contest = Contest.objects.filter(Q(key=contest_key) | Q(id=contest_key if str(contest_key).isdigit() else -1)).first()
            if not contest:
                return Response({'status': 404, 'error': f'Không tìm thấy cuộc thi {contest_key}.'}, status=404)

        oc, created = OrganizationContest.objects.get_or_create(
            organization=org, contest=contest,
            defaults={'is_official': request.data.get('is_official', True)}
        )
        log_audit(org, actor, 'LINK_CONTEST', contest.name, details=f"Gán contest nội bộ {contest.key} vào tổ chức")
        log_activity(org, actor, 'link_contest', 'contest', contest.key, f"Gán cuộc thi {contest.name}")
        return Response({'status': 200, 'message': f'Đã liên kết cuộc thi "{contest.name}" vào tổ chức!'})

    def delete(self, request, slug):
        """Unlink a contest from this organization."""
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'contest.create'):
            return Response({'status': 403, 'error': 'Không có quyền xóa cuộc thi khỏi tổ chức.'}, status=403)

        contest_key = request.data.get('contest_key') or request.GET.get('contest_key')
        oc = OrganizationContest.objects.filter(organization=org, contest__key=contest_key).first()
        if not oc:
            oc = OrganizationContest.objects.filter(organization=org, contest_id=contest_key if str(contest_key).isdigit() else -1).first()
        if not oc:
            return Response({'status': 404, 'error': 'Không tìm thấy cuộc thi trong tổ chức.'}, status=404)

        name = oc.contest.name
        oc.delete()
        log_audit(org, actor, 'UNLINK_CONTEST', name, details=f"Gỡ cuộc thi {contest_key} khỏi tổ chức")
        return Response({'status': 200, 'message': f'Đã gỡ cuộc thi "{name}" khỏi tổ chức thành công.'})

# ── 6. PROBLEMS ──────────────────────────────────────────────────────────────
class OrganizationProblemsAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)

        # Check if caller wants list of available problems to link (for Admin)
        if request.GET.get('available') == '1':
            actor = resolve_user(request)
            if not user_has_org_permission(actor, org, 'problem.create'):
                return Response({'status': 403, 'error': 'Không có quyền quản lý bài tập.'}, status=403)
            linked_ids = OrganizationProblem.objects.filter(organization=org).values_list('problem_id', flat=True)
            available = Problem.objects.exclude(id__in=linked_ids).order_by('code')[:80]
            data = [{'id': p.id, 'code': p.code, 'name': p.name, 'points': p.points, 'difficulty': p.difficulty} for p in available]
            return Response({'status': 200, 'data': data})

        search = request.GET.get('search', '').strip()
        difficulty = request.GET.get('difficulty', '').strip()

        org_probs = OrganizationProblem.objects.filter(organization=org).select_related('problem')
        results = []
        for op in org_probs:
            p = op.problem
            if search and (search.lower() not in p.code.lower() and search.lower() not in p.name.lower()):
                continue

            # Compute solved count
            solved_count = Submission.objects.filter(problem=p, result='AC').values('user').distinct().count()
            total_sub = Submission.objects.filter(problem=p).count()
            ac_rate = round((solved_count / total_sub * 100) if total_sub > 0 else 0.0, 1)

            diff = 'Easy' if p.points <= 100 else ('Medium' if p.points <= 200 else 'Hard')
            if difficulty and difficulty.lower() != 'all' and diff.lower() != difficulty.lower():
                continue

            results.append({
                'id': p.id,
                'code': p.code,
                'name': p.name,
                'points': p.points,
                'time_limit': p.time_limit,
                'memory_limit': p.memory_limit,
                'difficulty': diff,
                'is_internal': p.is_organization_private,
                'solved_count': solved_count,
                'total_submissions': total_sub,
                'ac_rate': ac_rate
            })
        return Response({'status': 200, 'data': results})

    def post(self, request, slug):
        """Link existing problem or create new internal problem for organization."""
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'problem.create'):
            return Response({'status': 403, 'error': 'Không có quyền tạo hoặc liên kết bài tập trong tổ chức.'}, status=403)

        data = request.data
        code = data.get('code', '').strip().upper()
        name = data.get('name', '').strip()
        is_new = data.get('is_new', False) or (name and not code)

        # Mode 1: Create a brand-new internal problem scoped ONLY to this organization
        if is_new or (name and not Problem.objects.filter(code=code).exists()):
            if not name:
                return Response({'status': 400, 'error': 'Tên bài tập không được để trống.'}, status=400)
            
            import re, time, os
            from django.conf import settings

            if not code:
                base_code = re.sub(r'[^A-Z0-9]', '', name.upper())[:6] or org.slug.upper()[:5]
                code = f"{base_code}_{int(time.time()) % 10000}"
            else:
                code = re.sub(r'[^A-Z0-9_]', '', code)

            if Problem.objects.filter(code=code).exists():
                return Response({'status': 400, 'error': f'Mã bài tập "{code}" đã tồn tại. Vui lòng chọn mã khác.'}, status=400)

            # Internal problem: is_public=False, is_organization_private=True
            prob = Problem.objects.create(
                code=code,
                name=name,
                description=data.get('description', f'Bài tập nội bộ của tổ chức {org.short_name or org.name}.'),
                time_limit=float(data.get('time_limit', 1.0)),
                memory_limit=int(data.get('memory_limit', 262144)),
                points=float(data.get('points', 100.0)),
                difficulty=data.get('difficulty', 'medium'),
                is_public=False,
                is_organization_private=True,
                status='published'
            )
            prob.organizations.add(org)
            if actor and hasattr(actor, 'profile'):
                prob.authors.add(actor.profile)

            # Ensure cases directory exists for judge
            prob_cases_dir = os.path.join(settings.DMOJ_PROBLEM_DATA_ROOT, code, 'cases')
            os.makedirs(prob_cases_dir, exist_ok=True)

            OrganizationProblem.objects.get_or_create(organization=org, problem=prob)
            log_audit(org, actor, 'CREATE_ORG_PROBLEM', prob.code, details=f"Tạo bài tập nội bộ {prob.code} - {prob.name}")
            log_activity(org, actor, 'create_problem', 'problem', prob.code, f"Tạo bài tập nội bộ {prob.name}")
            return Response({'status': 201, 'message': f'Đã tạo bài tập nội bộ "{prob.code} - {prob.name}" thành công!', 'data': {'code': prob.code, 'name': prob.name}}, status=201)

        # Mode 2: Link existing problem by code
        prob = Problem.objects.filter(code=code).first()
        if not prob:
            return Response({'status': 404, 'error': f'Không tìm thấy bài tập mã {code}.'}, status=404)

        OrganizationProblem.objects.get_or_create(organization=org, problem=prob)
        prob.organizations.add(org)
        log_audit(org, actor, 'LINK_PROBLEM', prob.code, details=f"Gán bài {prob.code} vào tổ chức")
        log_activity(org, actor, 'link_problem', 'problem', prob.code, f"Thêm bài tập {prob.name}")
        return Response({'status': 200, 'message': f'Đã liên kết bài tập "{prob.code} - {prob.name}"!'})

    def delete(self, request, slug):
        """Unlink a problem from this organization."""
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'problem.create'):
            return Response({'status': 403, 'error': 'Không có quyền xóa bài tập khỏi tổ chức.'}, status=403)

        code = request.data.get('code') or request.GET.get('code')
        op = OrganizationProblem.objects.filter(organization=org, problem__code=code).first()
        if not op:
            return Response({'status': 404, 'error': f'Không tìm thấy bài tập "{code}" trong tổ chức.'}, status=404)

        prob_name = op.problem.name
        op.delete()
        log_audit(org, actor, 'UNLINK_PROBLEM', code, details=f"Gỡ bài {code} khỏi tổ chức")
        log_activity(org, actor, 'unlink_problem', 'problem', code, f"Gỡ bài tập {prob_name}")
        return Response({'status': 200, 'message': f'Đã gỡ bài tập "{code} - {prob_name}" khỏi tổ chức thành công!'})

# ── 7. RANKING ───────────────────────────────────────────────────────────────
class OrganizationRankingAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        members = OrganizationMember.objects.filter(
            organization=org, status='active'
        ).select_related('user', 'user__profile', 'role').order_by('-user__profile__rating', '-user__profile__problem_count')

        rank = 1
        objects = []
        for m in members:
            p = getattr(m.user, 'profile', None)
            objects.append({
                'rank': rank,
                'username': m.user.username,
                'display_name': m.user.get_full_name() or m.user.username,
                'role': m.role.name,
                'role_color': m.role.color,
                'rating': p.rating if p and p.rating else 1500,
                'display_rank': p.display_rank if p else 'Pupil',
                'is_verified': bool(p.is_verified) if p else False,
                'solved_count': p.problem_count if p else 0,
                'points': p.points if p else 0.0
            })
            rank += 1

        return Response({'status': 200, 'data': {'objects': objects, 'total': len(objects)}})

# ── 8. BLOG / POSTS ──────────────────────────────────────────────────────────
class OrganizationBlogAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        posts = OrganizationPost.objects.filter(organization=org).select_related('author')
        serializer = OrganizationPostSerializer(posts, many=True)
        return Response({'status': 200, 'data': serializer.data})

    def post(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'blog.create'):
            return Response({'status': 403, 'error': 'Không có quyền đăng bài viết.'}, status=403)

        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()
        if not title or not content:
            return Response({'status': 400, 'error': 'Tiêu đề và nội dung bài viết không được để trống.'}, status=400)

        post = OrganizationPost.objects.create(
            organization=org, author=actor, title=title, content=content,
            summary=request.data.get('summary', title[:120]),
            is_pinned=bool(request.data.get('is_pinned', False))
        )
        log_audit(org, actor, 'CREATE_BLOG_POST', post.title)
        log_activity(org, actor, 'create_post', 'post', str(post.id), post.title)
        serializer = OrganizationPostSerializer(post)
        return Response({'status': 201, 'message': 'Đăng bài viết thành công!', 'data': serializer.data}, status=201)

class OrganizationBlogDetailAPIView(OrganizationAPIView):
    def get(self, request, slug, post_id):
        org = get_object_or_404(Organization, slug=slug)
        post = get_object_or_404(OrganizationPost, organization=org, id=post_id)
        serializer = OrganizationPostSerializer(post)
        return Response({'status': 200, 'data': serializer.data})

    def delete(self, request, slug, post_id):
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'blog.edit'):
            return Response({'status': 403, 'error': 'Không có quyền xóa bài viết.'}, status=403)
        post = get_object_or_404(OrganizationPost, organization=org, id=post_id)
        post.delete()
        log_audit(org, actor, 'DELETE_BLOG_POST', f"Post #{post_id}")
        return Response({'status': 200, 'message': 'Đã xóa bài viết.'})

# ── 9. ANNOUNCEMENTS ─────────────────────────────────────────────────────────
class OrganizationAnnouncementsAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        ann = OrganizationAnnouncement.objects.filter(organization=org, is_active=True).select_related('author')
        serializer = OrganizationAnnouncementSerializer(ann, many=True)
        return Response({'status': 200, 'data': serializer.data})

    def post(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'announcement.create'):
            return Response({'status': 403, 'error': 'Không có quyền tạo thông báo.'}, status=403)

        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()
        if not title:
            return Response({'status': 400, 'error': 'Tiêu đề thông báo không được để trống.'}, status=400)

        ann = OrganizationAnnouncement.objects.create(
            organization=org, author=actor, title=title, content=content,
            badge_type=request.data.get('badge_type', 'info')
        )
        log_audit(org, actor, 'CREATE_ANNOUNCEMENT', ann.title)
        log_activity(org, actor, 'create_announcement', 'announcement', str(ann.id), ann.title)
        serializer = OrganizationAnnouncementSerializer(ann)
        return Response({'status': 201, 'message': 'Đăng thông báo thành công!', 'data': serializer.data}, status=201)

    def delete(self, request, slug):
        """Delete an announcement from the organization."""
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'announcement.create'):
            return Response({'status': 403, 'error': 'Không có quyền xóa thông báo.'}, status=403)

        ann_id = request.data.get('id') or request.GET.get('id')
        ann = get_object_or_404(OrganizationAnnouncement, organization=org, id=ann_id)
        ann_title = ann.title
        ann.delete()
        log_audit(org, actor, 'DELETE_ANNOUNCEMENT', ann_title, details=f"Xóa thông báo #{ann_id}")
        return Response({'status': 200, 'message': f'Đã xóa thông báo "{ann_title}" thành công!'})

# ── 10. ACTIVITY STREAM ──────────────────────────────────────────────────────
class OrganizationActivityAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        acts = OrganizationActivity.objects.filter(organization=org).select_related('user')[:50]
        serializer = OrganizationActivitySerializer(acts, many=True)
        return Response({'status': 200, 'data': serializer.data})

# ── 11. ADMIN APIS: STATS, ROLES, PERMISSIONS, INVITATIONS, AUDIT-LOG ────────
class OrganizationAdminStatsAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'organization.view'):
            return Response({'status': 403, 'error': 'Không có quyền truy cập quản trị.'}, status=403)

        return Response({
            'status': 200,
            'data': {
                'members_count': org.org_members.filter(status='active').count(),
                'problems_count': org.org_problems.count(),
                'contests_count': org.org_contests.count(),
                'posts_count': org.org_posts.count(),
                'announcements_count': org.org_announcements.filter(is_active=True).count(),
                'pending_invitations': org.org_invitations.filter(status='pending').count()
            }
        })

class OrganizationAdminRolesAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        roles = OrganizationRole.objects.filter(organization=org).prefetch_related('permissions')
        serializer = OrganizationRoleSerializer(roles, many=True)
        return Response({'status': 200, 'data': serializer.data})

class OrganizationAdminInvitationsAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        invs = OrganizationInvitation.objects.filter(organization=org).select_related('inviter', 'role')
        serializer = OrganizationInvitationSerializer(invs, many=True)
        return Response({'status': 200, 'data': serializer.data})

    def post(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'member.add'):
            return Response({'status': 403, 'error': 'Không có quyền gửi lời mời.'}, status=403)

        invitee = request.data.get('username', '').strip()
        email = request.data.get('email', '').strip()
        role_id = request.data.get('role_id')
        role = OrganizationRole.objects.filter(organization=org, id=role_id).first() or OrganizationRole.objects.filter(organization=org, is_default=True).first()

        inv = OrganizationInvitation.objects.create(
            organization=org, inviter=actor, invitee_username=invitee, email=email, role=role
        )
        log_audit(org, actor, 'SEND_INVITATION', invitee, details=f"Mời tham gia vai trò {role.name}")
        return Response({'status': 201, 'message': f'Đã gửi lời mời tới {invitee}!'})

class OrganizationAdminAuditLogAPIView(OrganizationAPIView):
    def get(self, request, slug):
        org = get_object_or_404(Organization, slug=slug)
        actor = resolve_user(request)
        if not user_has_org_permission(actor, org, 'organization.edit'):
            return Response({'status': 403, 'error': 'Không có quyền xem nhật ký kiểm toán.'}, status=403)

        logs = OrganizationAuditLog.objects.filter(organization=org).select_related('actor')[:100]
        serializer = OrganizationAuditLogSerializer(logs, many=True)
        return Response({'status': 200, 'data': serializer.data})
