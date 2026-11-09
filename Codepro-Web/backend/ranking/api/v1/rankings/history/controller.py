from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from backend.ranking.services.rating_service import RatingService
from .serializer import UserRatingProfileSerializer

class RatingHistoryController(APIView):
    def get(self, request, username_or_id):
        data = RatingService.get_user_rating_profile(username_or_id)
        if not data:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserRatingProfileSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)