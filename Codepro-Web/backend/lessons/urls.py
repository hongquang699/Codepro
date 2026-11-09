from django.urls import path
from .views import LessonsListView

urlpatterns = [
    path('', LessonsListView.as_view(), name='lessons-list'),
]
