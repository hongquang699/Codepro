from rest_framework import serializers
from django.contrib.auth.models import User
from backend.judge.models import Organization, Contest, Problem, Profile
from .models import (
    OrganizationRole, OrganizationPermission, OrganizationMember,
    OrganizationContest, OrganizationProblem, OrganizationPost,
    OrganizationAnnouncement, OrganizationActivity, OrganizationAuditLog,
    OrganizationInvitation
)

class OrganizationRoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationRole
        fields = ['id', 'name', 'color', 'is_default', 'permissions', 'member_count', 'created_at']

    def get_permissions(self, obj):
        return list(obj.permissions.values_list('permission', flat=True))

    def get_member_count(self, obj):
        return obj.members.filter(status='active').count()

class OrganizationDetailSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    problem_count = serializers.SerializerMethodField()
    contest_count = serializers.SerializerMethodField()
    user_status = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            'id', 'slug', 'name', 'short_name', 'about', 'description',
            'logo', 'cover', 'website', 'is_open', 'verified',
            'member_count', 'problem_count', 'contest_count',
            'owner', 'user_status', 'user_role', 'can_manage', 'creation_date'
        ]

    def get_owner(self, obj):
        owner_id = getattr(obj, 'owner_id', None)
        if owner_id:
            u = User.objects.filter(id=owner_id).first()
            if u:
                return {'id': u.id, 'username': u.username, 'display_name': u.get_full_name() or u.username}
        return None

    def get_member_count(self, obj):
        count = obj.org_members.filter(status='active').count()
        return max(count, getattr(obj, 'member_count', 0) or 0)

    def get_problem_count(self, obj):
        return obj.org_problems.count()

    def get_contest_count(self, obj):
        return obj.org_contests.count()

    def _get_request_user(self):
        req = self.context.get('request')
        if not req:
            return None
        if hasattr(req, 'user') and req.user and req.user.is_authenticated and req.user.is_active:
            return req.user
        return None

    def get_user_status(self, obj):
        u = self._get_request_user()
        if not u:
            return None
        if u.is_staff or u.is_superuser:
            return 'active'
        m = obj.org_members.filter(user=u).first()
        return m.status if m else 'none'

    def get_user_role(self, obj):
        u = self._get_request_user()
        if not u:
            return None
        if u.is_staff or u.is_superuser:
            return 'System Administrator'
        m = obj.org_members.filter(user=u, status='active').select_related('role').first()
        return m.role.name if m else None

    def get_can_manage(self, obj):
        user = self._get_request_user()
        if not user:
            return False
        from .permissions import user_has_org_permission
        return user_has_org_permission(user, obj, 'organization.edit')

class OrganizationMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    display_name = serializers.SerializerMethodField()
    role_name = serializers.CharField(source='role.name')
    role_color = serializers.CharField(source='role.color')
    rating = serializers.SerializerMethodField()
    display_rank = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    solved_count = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationMember
        fields = [
            'id', 'user_id', 'username', 'display_name',
            'role_id', 'role_name', 'role_color', 'status',
            'rating', 'display_rank', 'is_verified', 'solved_count', 'joined_at'
        ]

    def get_display_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_rating(self, obj):
        p = getattr(obj.user, 'profile', None)
        return p.rating if p and p.rating else 1500

    def get_display_rank(self, obj):
        p = getattr(obj.user, 'profile', None)
        return p.display_rank if p else 'Pupil'

    def get_is_verified(self, obj):
        p = getattr(obj.user, 'profile', None)
        return bool(p.is_verified) if p else False

    def get_solved_count(self, obj):
        p = getattr(obj.user, 'profile', None)
        return p.problem_count if p else 0

class OrganizationPostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_display_name = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationPost
        fields = [
            'id', 'title', 'content', 'summary', 'is_pinned',
            'author_username', 'author_display_name', 'created_at', 'updated_at'
        ]

    def get_author_display_name(self, obj):
        return obj.author.get_full_name() or obj.author.username

class OrganizationAnnouncementSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = OrganizationAnnouncement
        fields = [
            'id', 'title', 'content', 'badge_type', 'is_active',
            'author_username', 'created_at'
        ]

class OrganizationActivitySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', default='System')

    class Meta:
        model = OrganizationActivity
        fields = [
            'id', 'username', 'action', 'target_type', 'target_id',
            'target_title', 'created_at'
        ]

class OrganizationAuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', default='System')

    class Meta:
        model = OrganizationAuditLog
        fields = [
            'id', 'actor_username', 'action', 'target', 'ip', 'details', 'created_at'
        ]

class OrganizationInvitationSerializer(serializers.ModelSerializer):
    inviter_username = serializers.CharField(source='inviter.username')
    role_name = serializers.CharField(source='role.name')

    class Meta:
        model = OrganizationInvitation
        fields = [
            'id', 'invitee_username', 'email', 'role_id', 'role_name',
            'inviter_username', 'status', 'created_at'
        ]
