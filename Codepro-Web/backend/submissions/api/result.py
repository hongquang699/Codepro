from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.result import ResultService

class SubmissionStatusPollingAPIView(APIView):
    def get(self, request, submission_id):
        data = ResultService.get_detail(submission_id)
        if not data:
            return Response({'error': 'Không tìm thấy bài nộp.'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'id': data['id'],
            'status': data['status'],
            'verdict': data['verdict'],
            'verdict_name': data['verdict_name'],
            'score': data['score'],
            'time': data['execution_time'],
            'memory': data['memory_used'],
            'finished': data['status'] == 'FINISHED'
        }, status=status.HTTP_200_OK)
