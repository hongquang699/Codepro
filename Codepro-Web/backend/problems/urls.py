from django.urls import path
from .views import ProblemsListView

urlpatterns = [
    path('', ProblemsListView.as_view(), name='problems-list'),
]
