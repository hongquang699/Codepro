from django.urls import path

from . import views

urlpatterns = [
    path('penalties', views.MyPenaltiesView.as_view()),
    path('appeals', views.MyAppealsView.as_view()),
]
