from django.urls import path
from .controller import RatingLeaderboardController

urlpatterns = [
    path('', RatingLeaderboardController.as_view(), name='rating_leaderboard'),
]