from django.urls import path
from .controller import SchoolRankingController

urlpatterns = [
    path('', SchoolRankingController.as_view(), name='school_rankings'),
    path('<str:school_name>/', SchoolRankingController.as_view(), name='school_students_ranking'),
]