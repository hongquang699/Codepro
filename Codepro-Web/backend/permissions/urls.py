from django.urls import path
from .views import PermissionsListView

urlpatterns = [
    path('', PermissionsListView.as_view(), name='permissions-list'),
]
