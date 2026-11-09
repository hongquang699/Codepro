from django.urls import path
from .controller import GlobalRankingController

urlpatterns = [
    path('', GlobalRankingController.as_view(), name='global_rankings'),
]