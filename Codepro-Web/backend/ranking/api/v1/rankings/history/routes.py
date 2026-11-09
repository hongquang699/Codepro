from django.urls import path
from .controller import RatingHistoryController

urlpatterns = [
    path('<str:username_or_id>/', RatingHistoryController.as_view(), name='user_rating_history'),
]