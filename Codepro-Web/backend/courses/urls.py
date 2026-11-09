from django.urls import path
from .views import CoursesListView

urlpatterns = [
    path('', CoursesListView.as_view(), name='courses-list'),
]
