from django.urls import path
from .controller import RankingStatisticsController

urlpatterns = [
    path('', RankingStatisticsController.as_view(), name='ranking_statistics'),
]