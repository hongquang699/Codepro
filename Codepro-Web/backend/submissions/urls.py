from django.urls import path
from .views import SubmissionsListView

urlpatterns = [
    path('', SubmissionsListView.as_view(), name='submissions-list'),
]
