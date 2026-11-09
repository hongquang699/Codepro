from django.db.models.signals import post_save
from django.dispatch import receiver

from backend.judge.models import Submission

from .models import ProblemRelease, SubmissionVersion


@receiver(post_save, sender=Submission)
def pin_published_problem_version(sender, instance, created, **kwargs):
    if not created:
        return
    release = ProblemRelease.objects.filter(problem_id=instance.problem_id).first()
    if release:
        SubmissionVersion.objects.get_or_create(submission=instance, defaults={'version': release.version})
