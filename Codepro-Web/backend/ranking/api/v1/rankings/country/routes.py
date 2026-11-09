from django.urls import path
from .controller import CountryRankingController

urlpatterns = [
    path('', CountryRankingController.as_view(), name='country_rankings'),
    path('<str:country_name>/', CountryRankingController.as_view(), name='country_users_ranking'),
]