from rest_framework.response import Response
from rest_framework.views import APIView

class ForumListView(APIView):
    def get(self, request):
        return Response({'module': 'forum', 'items': []})
