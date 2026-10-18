import hmac
import json
from urllib import request as urlrequest

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.auth.security.token_auth import ExpiringTokenAuthentication
from backend.judge.models import Problem
from backend.judge.permissions.authentication import BearerTokenAuthentication, JudgeCookieAuthentication

from .models import ProblemVersion
from .service import initiate, publish, s3, validate_version


def can_edit(user, problem):
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if user.is_staff or user.is_superuser:
        return True
    if user.groups.filter(name='problem_editor').exists():
        return True
    return problem.authors.filter(user=user).exists()


class Authenticated(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


class StorageView(APIView):
    authentication_classes = [ExpiringTokenAuthentication, BearerTokenAuthentication,
        JudgeCookieAuthentication, SessionAuthentication]
    permission_classes = [Authenticated]

    def problem(self, request, code):
        problem = get_object_or_404(Problem, code=code)
        if not can_edit(request.user, problem):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied()
        return problem


class VersionsView(StorageView):
    def get(self, request, code):
        problem = self.problem(request, code)
        return Response([{'id': str(v.id), 'number': v.number, 'state': v.state,
            'sha256': v.sha256, 'size_bytes': v.size_bytes, 'manifest': v.manifest,
            'error': v.error, 'published_at': v.published_at}
            for v in problem.storage_versions.all()])

    def post(self, request, code):
        problem = self.problem(request, code)
        try:
            version, upload = initiate(problem, request.user)
        except RuntimeError as exc:
            return Response({'error': str(exc)}, status=503)
        return Response({'id': str(version.id), 'number': version.number,
            'upload_url': upload['url'], 'upload_fields': upload['fields'],
            'method': 'POST', 'content_type': 'application/zip',
            'expires_in': 900}, status=201)


class VersionView(StorageView):
    def get(self, request, code, version_id):
        problem = self.problem(request, code)
        version = get_object_or_404(ProblemVersion, problem=problem, pk=version_id)
        return Response({'id': str(version.id), 'number': version.number, 'state': version.state,
            'sha256': version.sha256, 'size_bytes': version.size_bytes,
            'manifest': version.manifest, 'error': version.error})


class CompleteView(StorageView):
    def post(self, request, code, version_id):
        problem = self.problem(request, code)
        version = get_object_or_404(ProblemVersion, problem=problem, pk=version_id)
        if version.state != ProblemVersion.State.PENDING:
            return Response({'error': 'Upload already completed'}, status=409)
        try:
            head = s3().head_object(Bucket=settings.PROBLEM_STORAGE_PRIVATE_BUCKET, Key=version.private_key)
            if head['ContentLength'] > 20 * 1024 * 1024:
                return Response({'error': 'ZIP exceeds 20 MiB'}, status=400)
            if not settings.PROBLEM_STORAGE_QUEUE_URL or not settings.PROBLEM_STORAGE_INTERNAL_TOKEN:
                return Response({'error': 'Validation queue is not configured'}, status=503)
            payload = json.dumps({'version_id': str(version.id)}).encode('utf-8')
            req = urlrequest.Request(settings.PROBLEM_STORAGE_QUEUE_URL.rstrip('/') + '/enqueue',
                data=payload, headers={'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + settings.PROBLEM_STORAGE_INTERNAL_TOKEN})
            with urlrequest.urlopen(req, timeout=5):
                pass
        except Exception:
            return Response({'error': 'Upload or validation queue unavailable'}, status=503)
        return Response({'id': str(version.id), 'state': 'pending'}, status=202)


class PublishView(StorageView):
    def post(self, request, code, version_id):
        problem = self.problem(request, code)
        version = get_object_or_404(ProblemVersion, problem=problem, pk=version_id)
        try:
            version = publish(version)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=409)
        return Response({'id': str(version.id), 'state': version.state})


class InternalValidateView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        expected = settings.PROBLEM_STORAGE_INTERNAL_TOKEN
        provided = request.headers.get('Authorization', '').removeprefix('Bearer ')
        if not expected or not hmac.compare_digest(provided, expected):
            return Response(status=403)
        version_id = request.data.get('version_id')
        try:
            version = validate_version(version_id)
        except (ProblemVersion.DoesNotExist, ValueError):
            return Response({'error': 'Invalid version'}, status=400)
        except Exception:
            return Response({'error': 'Validation failed'}, status=500)
        return Response({'id': str(version.id), 'state': version.state})
