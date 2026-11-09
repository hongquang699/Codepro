from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from ...services.achievements import get_user_achievements

class ProfileAchievementsAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        achievements = get_user_achievements(user)
        unlocked_count = sum(1 for a in achievements if a['is_unlocked'])

        return Response({
            'status': 'success',
            'total': len(achievements),
            'unlocked_count': unlocked_count,
            'results': achievements
        })
