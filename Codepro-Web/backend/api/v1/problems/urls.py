from django.urls import path
from . import views

urlpatterns = [
    path('', views.ProblemListCreateAPI.as_view(), name='api1-problems-list-create'),
    path('<str:pk>', views.ProblemDetailAPI.as_view(), name='api1-problem-detail'),
    path('<str:pk>/statement', views.ProblemStatementAPI.as_view(), name='api1-problem-statement'),
    path('<str:pk>/testcases', views.ProblemTestcasesAPI.as_view(), name='api1-problem-testcases'),
    path('<str:pk>/testcases/upload', views.ProblemTestcasesUploadAPI.as_view(), name='api1-problem-testcases-upload'),
    path('<str:pk>/testcases/<str:tid>', views.ProblemTestcaseDetailAPI.as_view(), name='api1-problem-testcase-detail'),
    path('<str:pk>/checker', views.ProblemCheckerAPI.as_view(), name='api1-problem-checker'),
    path('<str:pk>/validator', views.ProblemValidatorAPI.as_view(), name='api1-problem-validator'),
    path('<str:pk>/solutions', views.ProblemSolutionsAPI.as_view(), name='api1-problem-solutions'),
    path('<str:pk>/solutions/test', views.ProblemSolutionsTestAPI.as_view(), name='api1-problem-solutions-test'),
    path('<str:pk>/preview', views.ProblemPreviewAPI.as_view(), name='api1-problem-preview'),
    path('<str:pk>/publish', views.ProblemPublishAPI.as_view(), name='api1-problem-publish'),
    path('<str:pk>/unpublish', views.ProblemUnpublishAPI.as_view(), name='api1-problem-unpublish'),
]
