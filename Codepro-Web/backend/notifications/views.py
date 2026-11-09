from rest_framework.response import Response
from rest_framework.views import APIView

class NotificationsListView(APIView):
    def get(self, request):
        return Response({'module': 'notifications', 'items': []})
