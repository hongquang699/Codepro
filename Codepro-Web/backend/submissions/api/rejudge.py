from rest_framework.response import Response
from rest_framework import status
from backend.judge.api.admin_views import JudgeAdminView
from ..services.rejudge import RejudgeService

class RejudgeAPIView(JudgeAdminView):
    def post(self, request, submission_id):
        ok, msg = RejudgeService.rejudge(submission_id, async_judge=True)
        if not ok:
            return Response({'error': msg}, status=status.HTTP_404_NOT_FOUND)
        self.audit(request, 'submission.rejudge', str(submission_id))
        return Response({'success': True, 'message': msg, 'submission_id': submission_id}, status=status.HTTP_200_OK)
