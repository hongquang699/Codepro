from rest_framework import serializers
from django.contrib.auth.models import User
from backend.judge.models import (
    Profile, Organization, Language, Problem, ProblemType,
    Contest, ContestProblem, ContestParticipation,
    Submission, SubmissionTestCase, Judge, RatingHistory,
    Clarification, BlogPost, Comment
)
from backend.judge.permissions.submissions import can_view_submission_details

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'name', 'slug', 'short_name', 'about', 'is_open', 'member_count']

class UserProfileSerializer(serializers.ModelSerializer):
    username   = serializers.CharField(source='user.username', read_only=True)
    email      = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name  = serializers.CharField(source='user.last_name', read_only=True)
    display_name = serializers.SerializerMethodField()
    is_staff   = serializers.BooleanField(source='user.is_staff', read_only=True)
    is_superuser = serializers.BooleanField(source='user.is_superuser', read_only=True)
    is_active  = serializers.BooleanField(source='user.is_active', read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    role       = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(source='user.date_joined', read_only=True)
    organizations = OrganizationSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'display_name',
            'about', 'timezone', 'points', 'performance_points', 'problem_count',
            'rating', 'display_rank', 'is_verified', 'role', 'is_staff', 'is_superuser', 'is_active',
            'organizations', 'date_joined'
        ]

    def get_role(self, obj):
        if obj.user.is_superuser or (obj.user.is_staff and obj.role == 'admin'):
            return 'admin'
        if obj.role == 'teacher' or obj.user.groups.filter(name='teacher').exists():
            return 'teacher'
        if obj.role == 'setter' or obj.user.is_staff:
            return 'setter'
        return obj.role if obj.role in ('user', 'teacher', 'setter') else 'user'

    def get_display_name(self, obj):
        full = obj.user.get_full_name()
        return full if full else obj.user.username


class PublicUserProfileSerializer(UserProfileSerializer):
    """Profile fields safe to expose on public user and ranking pages."""

    class Meta(UserProfileSerializer.Meta):
        fields = [
            'id', 'username', 'first_name', 'last_name', 'display_name',
            'about', 'timezone', 'points', 'performance_points', 'problem_count',
            'rating', 'display_rank', 'is_verified', 'role', 'organizations',
            'date_joined',
        ]

class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'key', 'name', 'short_name', 'common_name', 'ace_mode_name', 'is_active']

class ProblemTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProblemType
        fields = ['name', 'full_name']

class ProblemListSerializer(serializers.ModelSerializer):
    types = ProblemTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Problem
        fields = [
            'code', 'name', 'types', 'time_limit', 'memory_limit',
            'points', 'partial', 'is_public'
        ]

class ProblemDetailSerializer(serializers.ModelSerializer):
    types = ProblemTypeSerializer(many=True, read_only=True)
    authors = serializers.SlugRelatedField(many=True, read_only=True, slug_field='user__username')

    class Meta:
        model = Problem
        fields = [
            'code', 'name', 'description', 'types', 'time_limit',
            'memory_limit', 'points', 'partial', 'short_circuit',
            'is_public', 'authors', 'date'
        ]

class SubmissionTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubmissionTestCase
        fields = ['case', 'status', 'time', 'memory', 'points', 'total_points', 'feedback']

class SubmissionListSerializer(serializers.ModelSerializer):
    problem = serializers.CharField(source='problem.code')
    user = serializers.CharField(source='user.user.username')
    language = serializers.CharField(source='language.key')

    class Meta:
        model = Submission
        fields = [
            'id', 'problem', 'user', 'date', 'time', 'memory',
            'points', 'result', 'status', 'language'
        ]

class SubmissionDetailSerializer(serializers.ModelSerializer):
    problem = serializers.CharField(source='problem.code')
    user = serializers.CharField(source='user.user.username')
    language = serializers.CharField(source='language.name')
    source = serializers.SerializerMethodField()
    error = serializers.SerializerMethodField()
    test_cases = serializers.SerializerMethodField()

    def _can_view_private(self, obj):
        request = self.context.get('request')
        return can_view_submission_details(getattr(request, 'user', None), obj)

    def get_source(self, obj):
        if self._can_view_private(obj):
            return obj.source or ""
        return "[Mã nguồn được bảo mật theo quy chế cuộc thi]"

    def get_error(self, obj):
        return obj.error if self._can_view_private(obj) else ''

    def get_test_cases(self, obj):
        if not self._can_view_private(obj):
            return []
        return SubmissionTestCaseSerializer(obj.test_cases.all(), many=True).data

    class Meta:
        model = Submission
        fields = [
            'id', 'problem', 'user', 'date', 'time', 'memory',
            'points', 'result', 'status', 'language', 'source',
            'error', 'is_rejudged', 'test_cases'
        ]

class ContestProblemSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='problem.code')
    name = serializers.CharField(source='problem.name')

    class Meta:
        model = ContestProblem
        fields = ['order', 'output_prefix', 'code', 'name', 'points', 'partial']

class ContestListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contest
        fields = [
            'key', 'name', 'start_time', 'end_time', 'time_limit',
            'is_rated', 'format_name', 'is_visible', 'display_target'
        ]

class ContestDetailSerializer(serializers.ModelSerializer):
    problems = ContestProblemSerializer(source='contest_problems', many=True, read_only=True)

    class Meta:
        model = Contest
        fields = [
            'key', 'name', 'description', 'start_time', 'end_time',
            'time_limit', 'is_rated', 'format_name', 'is_visible', 'display_target',
            'hide_scoreboard', 'problems'
        ]

class JudgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Judge
        fields = [
            'name', 'online', 'start_time', 'ping', 'load',
            'last_seen', 'runtime_versions'
        ]

class ClarificationSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.user.username', read_only=True)
    problem_code = serializers.CharField(source='problem.code', read_only=True)
    contest_key = serializers.CharField(source='contest.key', read_only=True)
    answered_by_name = serializers.CharField(source='answered_by.user.username', read_only=True)

    class Meta:
        model = Clarification
        fields = [
            'id', 'user', 'problem_code', 'contest_key',
            'question', 'answer', 'is_public', 'date',
            'answered_at', 'answered_by_name'
        ]

class RatingHistorySerializer(serializers.ModelSerializer):
    contest_name = serializers.CharField(source='contest.name', read_only=True)
    contest_key = serializers.CharField(source='contest.key', read_only=True)

    class Meta:
        model = RatingHistory
        fields = [
            'id', 'contest_key', 'contest_name',
            'rating', 'volatility', 'ranking', 'last_rated'
        ]

class BlogPostSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.user.username', read_only=True)

    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'author_name',
            'body', 'publish_on', 'is_visible'
        ]

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.user.username', read_only=True)
    author_rank = serializers.CharField(source='author.display_rank', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'author_name', 'author_rank',
            'page', 'body', 'time', 'parent'
        ]

class RankingUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    display_name = serializers.SerializerMethodField()
    solved_count = serializers.IntegerField(source='problem_count')
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = Profile
        fields = [
            'username', 'display_name', 'rating', 'display_rank',
            'points', 'solved_count', 'is_verified'
        ]

    def get_display_name(self, obj):
        full = obj.user.get_full_name()
        return full if full else obj.user.username

