from django.urls import path
from .controller import ContestScoreboardController, ContestRatingComputeController

urlpatterns = [
    path('<str:contest_id>/', ContestScoreboardController.as_view(), name='contest_scoreboard'),
    path('<int:contest_id>/compute-ratings/', ContestRatingComputeController.as_view(), name='contest_compute_ratings'),
]