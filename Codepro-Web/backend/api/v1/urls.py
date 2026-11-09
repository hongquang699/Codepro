"""
CodeProOJ API v1 URL Routing
"""

from django.urls import path, include
from .home_views import HomeSummaryAPIView

urlpatterns = [
    path('problems/', include('backend.api.v1.problems.urls')),
    path('problems', include('backend.api.v1.problems.urls')),
    path('home/summary', HomeSummaryAPIView.as_view(), name='home-summary'),
    path('home/summary/', HomeSummaryAPIView.as_view(), name='home-summary-slash'),
]
