from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from ...services.rating import get_user_rating, get_rating_history

class ProfileRatingAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        rating_data = get_user_rating(user)
        return Response({
            'status': 'success',
            'data': rating_data
        })


class ProfileRatingHistoryAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        history = get_rating_history(user)
        return Response({
            'status': 'success',
            'history': history
        })
