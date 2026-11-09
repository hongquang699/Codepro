from django.urls import path
from .controller import UserRankingController

urlpatterns = [
    path('<str:username_or_id>/', UserRankingController.as_view(), name='user_ranking_detail'),
]