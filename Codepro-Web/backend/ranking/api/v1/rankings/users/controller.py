from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from backend.ranking.models.ranking import GlobalRanking
from backend.ranking.models.rating import UserRating
from .serializer import UserRankingDetailSerializer

class UserRankingController(APIView):
    def get(self, request, username_or_id):
        user = None
        if str(username_or_id).isdigit():
            user = User.objects.filter(id=int(username_or_id)).first()
        if not user:
            user = User.objects.filter(username=str(username_or_id)).first()

        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        rank_obj = GlobalRanking.objects.filter(user=user).first()
        rating_obj = UserRating.objects.filter(user=user).first()

        current_rating = rating_obj.current_rating if rating_obj else (user.profile.rating if hasattr(user, 'profile') else 1500)
        max_rating = rating_obj.max_rating if rating_obj else current_rating
        tier_info = UserRating.get_tier_info(current_rating)

        data = {
            'user_id': user.id,
            'username': user.username,
            'global_rank': rank_obj.rank if rank_obj else 9999,
            'rating': current_rating,
            'max_rating': max_rating,
            'tier': tier_info['tier'],
            'tier_color': tier_info['color'],
            'badge': tier_info['badge'],
            'score': rank_obj.score if rank_obj else 0.0,
            'solved': rank_obj.solved if rank_obj else 0,
            'submissions': rank_obj.submissions if rank_obj else 0,
            'contests_count': rating_obj.contests_participated if rating_obj else 0,
            'country': rank_obj.country if rank_obj else 'Vietnam',
            'school': rank_obj.school if rank_obj else '',
        }
        serializer = UserRankingDetailSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)