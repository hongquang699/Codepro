from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from ...services.activity import get_user_activity

class ProfileActivityAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        limit = int(request.GET.get('limit', 30))
        activities = get_user_activity(user, limit=limit)

        return Response({
            'status': 'success',
            'total': len(activities),
            'results': activities
        })
