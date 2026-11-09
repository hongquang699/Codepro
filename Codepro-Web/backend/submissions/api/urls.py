from django.urls import path
from .submit import SubmitAPIView
from .detail import SubmissionDetailAPIView
from .list import SubmissionListAPIView
from .testcase import SubmissionTestCaseAPIView
from .result import SubmissionStatusPollingAPIView
from .rejudge import RejudgeAPIView

urlpatterns = [
    # Submissions List & Submit
    path('', SubmissionListAPIView.as_view(), name='submissions_list'),
    path('submit/', SubmitAPIView.as_view(), name='submissions_submit_post'),

    # Submission Detail, Status & Testcases
    path('<int:submission_id>/', SubmissionDetailAPIView.as_view(), name='submission_detail'),
    path('<int:submission_id>', SubmissionDetailAPIView.as_view(), name='submission_detail_noslash'),
    path('<int:submission_id>/testcases/', SubmissionTestCaseAPIView.as_view(), name='submission_testcases'),
    path('<int:submission_id>/status/', SubmissionStatusPollingAPIView.as_view(), name='submission_status_poll'),
    path('<int:submission_id>/status', SubmissionStatusPollingAPIView.as_view(), name='submission_status_poll_noslash'),
    path('<int:submission_id>/result/', SubmissionDetailAPIView.as_view(), name='submission_result'),
    path('<int:submission_id>/result', SubmissionDetailAPIView.as_view(), name='submission_result_noslash'),
    path('<int:submission_id>/rejudge/', RejudgeAPIView.as_view(), name='submission_rejudge'),

    # Contextual Lists
    path('users/<str:username>/', SubmissionListAPIView.as_view(), name='user_submissions_list'),
    path('problems/<str:problem_id>/', SubmissionListAPIView.as_view(), name='problem_submissions_list'),
    path('contests/<str:contest_id>/', SubmissionListAPIView.as_view(), name='contest_submissions_list'),
]
