from django.urls import path
from .views import AchievementsListView

urlpatterns = [
    path('', AchievementsListView.as_view(), name='achievements-list'),
]
