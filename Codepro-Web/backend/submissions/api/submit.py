from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from backend.judge.permissions.authentication import BearerTokenAuthentication, JudgeCookieAuthentication
from ..services.submit import SubmitService

class SubmitAPIView(APIView):
    authentication_classes = [TokenAuthentication, BearerTokenAuthentication, JudgeCookieAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data or {}
        problem_id = data.get('problem_id') or data.get('problem')
        language_id = data.get('language_id') or data.get('language')
        source_code = data.get('source_code') or data.get('source')
        contest_id = data.get('contest_id') or data.get('contest')

        res = SubmitService.submit(
            user=request.user,
            problem_id=problem_id,
            language_id=language_id,
            source_code=source_code,
            contest_id=contest_id,
            async_judge=True
        )

        if not res.get('success'):
            return Response({'error': res.get('error')}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': True,
            'id': res['id'],
            'submission_id': res['id'],
            'status': res['status'],
            'problem': res.get('problem'),
            'language': res.get('language')
        }, status=status.HTTP_201_CREATED)
