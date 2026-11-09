from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from backend.ranking.services.rating_service import RatingService
from .serializer import RatingLeaderboardResponseSerializer

class RatingLeaderboardController(APIView):
    def get(self, request):
        try:
            page = int(request.query_params.get('page', 1))
            page_size = min(100, int(request.query_params.get('page_size', 50)))
        except ValueError:
            page, page_size = 1, 50

        tier = request.query_params.get('tier')
        search = request.query_params.get('search')

        data = RatingService.get_leaderboard(page=page, page_size=page_size, tier=tier, search=search)
        serializer = RatingLeaderboardResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)