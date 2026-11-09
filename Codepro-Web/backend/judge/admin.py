from django.contrib import admin
from .models import (
    Profile, Organization, Language, ProblemType, ProblemGroup,
    Problem, Contest, ContestProblem, ContestParticipation,
    Judge, Submission, SubmissionTestCase, RatingHistory,
    BlogPost, Comment
)

admin.site.register(Profile)
admin.site.register(Organization)
admin.site.register(Language)
admin.site.register(ProblemType)
admin.site.register(ProblemGroup)
admin.site.register(Problem)
admin.site.register(Contest)
admin.site.register(ContestProblem)
admin.site.register(ContestParticipation)
admin.site.register(Judge)
admin.site.register(Submission)
admin.site.register(SubmissionTestCase)
admin.site.register(RatingHistory)
admin.site.register(BlogPost)
admin.site.register(Comment)
