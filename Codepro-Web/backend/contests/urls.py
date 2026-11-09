from django.urls import path
from .views import ContestsListView

urlpatterns = [
    path('', ContestsListView.as_view(), name='contests-list'),
]
