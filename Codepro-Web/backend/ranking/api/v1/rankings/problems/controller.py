from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from backend.ranking.services.score_service import ScoreService
from .serializer import ProblemSolversResponseSerializer

class ProblemSolversController(APIView):
    def get(self, request, problem_code):
        limit = min(100, int(request.query_params.get('limit', 50)))
        data = ScoreService.get_problem_top_solvers(problem_code, limit=limit)
        if 'error' in data:
            return Response({'error': data['error']}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProblemSolversResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)