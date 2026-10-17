from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication
from backend.judge.permissions.authentication import BearerTokenAuthentication, JudgeCookieAuthentication
from ..services.result import ResultService

class SubmissionDetailAPIView(APIView):
    authentication_classes = [TokenAuthentication, BearerTokenAuthentication, JudgeCookieAuthentication, SessionAuthentication]

    def get(self, request, submission_id):
        data = ResultService.get_detail(submission_id, requesting_user=request.user)
        if not data:
            return Response({'error': 'Không tìm thấy bài nộp.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(data, status=status.HTTP_200_OK)
