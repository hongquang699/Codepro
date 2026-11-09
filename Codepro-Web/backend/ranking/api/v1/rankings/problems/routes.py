from django.urls import path
from .controller import ProblemSolversController

urlpatterns = [
    path('<str:problem_code>/', ProblemSolversController.as_view(), name='problem_top_solvers'),
]