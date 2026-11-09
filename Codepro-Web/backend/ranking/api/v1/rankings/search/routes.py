from django.urls import path
from .controller import RankingSearchController

urlpatterns = [
    path('', RankingSearchController.as_view(), name='ranking_search'),
]