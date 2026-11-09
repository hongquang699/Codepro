from django.urls import path
from .views import ForumListView

urlpatterns = [
    path('', ForumListView.as_view(), name='forum-list'),
]
