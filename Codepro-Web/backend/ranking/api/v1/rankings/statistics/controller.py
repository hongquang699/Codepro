from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Sum
from backend.ranking.models.ranking import GlobalRanking
from backend.ranking.models.rating import UserRating
from backend.judge.models import Submission
from .serializer import RankingStatisticsSerializer

class RankingStatisticsController(APIView):
    def get(self, request):
        total_users = GlobalRanking.objects.count()
        total_subs = Submission.objects.count()
        total_solved = GlobalRanking.objects.aggregate(s=Sum('solved'))['s'] or 0

        # Tier breakdown
        tiers = ['Legendary Grandmaster', 'Grandmaster', 'Master', 'Candidate Master', 'Expert', 'Specialist', 'Pupil', 'Newbie']
        tier_dist = {}
        for t in tiers:
            tier_dist[t] = UserRating.objects.filter(rank_tier__iexact=t).count()

        top_c = list(GlobalRanking.objects.values('country').annotate(count=Count('id')).order_by('-count')[:5])
        highest = UserRating.objects.order_by('-current_rating').first()
        highest_data = None
        if highest:
            info = UserRating.get_tier_info(highest.current_rating)
            highest_data = {
                'username': highest.user.username,
                'rating': highest.current_rating,
                'tier': info['tier'],
                'color': info['color']
            }

        data = {
            'total_ranked_users': total_users,
            'total_submissions': total_subs,
            'total_solved': total_solved,
            'tier_distribution': tier_dist,
            'top_countries': top_c,
            'highest_rated': highest_data
        }
        serializer = RankingStatisticsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)