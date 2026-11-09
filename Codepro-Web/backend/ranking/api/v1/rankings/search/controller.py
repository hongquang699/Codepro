from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from backend.ranking.models.ranking import GlobalRanking
from .serializer import SearchRankingItemSerializer

class RankingSearchController(APIView):
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({'results': []}, status=status.HTTP_200_OK)

        qs = GlobalRanking.objects.filter(
            Q(user__username__icontains=query) | Q(school__icontains=query)
        ).select_related('user').order_by('rank')[:20]

        results = []
        for r in qs:
            results.append({
                'user_id': r.user.id,
                'username': r.user.username,
                'rank': r.rank,
                'rating': r.rating,
                'tier': r.tier,
                'tier_color': '#3b82f6',
                'school': r.school
            })
        serializer = SearchRankingItemSerializer(results, many=True)
        return Response({'results': serializer.data}, status=status.HTTP_200_OK)