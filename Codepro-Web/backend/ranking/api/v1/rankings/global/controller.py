from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from backend.ranking.services.ranking_service import RankingService
from .serializer import GlobalRankingResponseSerializer

class GlobalRankingController(APIView):
    def get(self, request):
        try:
            page = int(request.query_params.get('page', 1))
            page_size = min(100, int(request.query_params.get('page_size', 50)))
        except ValueError:
            page, page_size = 1, 50

        country = request.query_params.get('country')
        school = request.query_params.get('school')
        org_id = request.query_params.get('organization')
        search = request.query_params.get('search')

        data = RankingService.get_global_rankings(
            page=page,
            page_size=page_size,
            country=country,
            school=school,
            org_id=org_id,
            search=search
        )
        serializer = GlobalRankingResponseSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)