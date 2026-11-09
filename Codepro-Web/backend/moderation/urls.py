from django.urls import path
from .views import ModerationListView

urlpatterns = [
    path('', ModerationListView.as_view(), name='moderation-list'),
]
