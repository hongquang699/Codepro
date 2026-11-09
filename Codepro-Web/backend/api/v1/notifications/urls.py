from django.urls import path
from rest_framework.response import Response
from rest_framework.views import APIView

class EndpointView(APIView):
    def get(self, request):
        return Response({'api_version': 'v1', 'resource': 'notifications'})

urlpatterns = [
    path('', EndpointView.as_view(), name='v1-notifications'),
]
