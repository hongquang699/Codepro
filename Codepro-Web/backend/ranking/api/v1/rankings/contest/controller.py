from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from backend.ranking.services.contest_ranking_service import ContestRankingService
from backend.ranking.tasks.compute_ratings import run_compute_ratings
from .serializer import ContestScoreboardSerializer

class ContestScoreboardController(APIView):
    def get(self, request, contest_id):
        live = request.query_params.get('live', 'true').lower() == 'true'
        data = ContestRankingService.get_scoreboard(contest_id, live=live)
        if 'error' in data:
            return Response({'error': data['error']}, status=status.HTTP_404_NOT_FOUND)
        serializer = ContestScoreboardSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ContestRatingComputeController(APIView):
    def post(self, request, contest_id):
        res = run_compute_ratings(contest_id)
        if res.get('error'):
            return Response(res, status=status.HTTP_400_BAD_REQUEST)
        return Response(res, status=status.HTTP_200_OK)