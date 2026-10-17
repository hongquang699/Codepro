from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication
from django.shortcuts import get_object_or_404
from backend.judge.models import Submission
from backend.judge.permissions.authentication import BearerTokenAuthentication, JudgeCookieAuthentication
from backend.judge.permissions.submissions import can_view_submission_details
from ..services.result import ResultService

class SubmissionTestCaseAPIView(APIView):
    authentication_classes = [TokenAuthentication, BearerTokenAuthentication, JudgeCookieAuthentication, SessionAuthentication]

    def get(self, request, submission_id):
        submission = get_object_or_404(Submission.objects.select_related('user__user'), id=submission_id)
        if not can_view_submission_details(request.user, submission):
            return Response({'error': 'Bạn không có quyền xem testcase của bài nộp này.'},
                            status=status.HTTP_403_FORBIDDEN)
        cases = ResultService.get_testcases(submission_id)
        return Response({'submission_id': submission_id, 'testcases': cases}, status=status.HTTP_200_OK)
