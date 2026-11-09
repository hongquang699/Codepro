from rest_framework.response import Response
from rest_framework.views import APIView

class ProblemsListView(APIView):
    def get(self, request):
        return Response({'module': 'problems', 'items': []})
