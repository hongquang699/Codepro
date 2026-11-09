import uuid

from django.conf import settings
from django.db import models


class ProblemVersion(models.Model):
    class State(models.TextChoices):
        PENDING = 'pending'
        VALIDATING = 'validating'
        READY = 'ready'
        REJECTED = 'rejected'
        PUBLISHED = 'published'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    problem = models.ForeignKey('judge.Problem', on_delete=models.PROTECT, related_name='storage_versions')
    number = models.PositiveIntegerField()
    state = models.CharField(max_length=16, choices=State.choices, default=State.PENDING)
    private_key = models.CharField(max_length=300, unique=True)
    public_key = models.CharField(max_length=300, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    manifest = models.JSONField(default=dict, blank=True)
    statement = models.TextField(blank=True)
    error = models.CharField(max_length=500, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['problem', 'number'], name='storage_version_number_unique')]
        ordering = ['-number']


class TestGroup(models.Model):
    version = models.ForeignKey(ProblemVersion, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=80)
    points = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['version', 'name'], name='storage_group_name_unique')]


class TestCase(models.Model):
    group = models.ForeignKey(TestGroup, on_delete=models.CASCADE, related_name='cases')
    name = models.CharField(max_length=128)
    input_path = models.CharField(max_length=260)
    output_path = models.CharField(max_length=260)
    input_sha256 = models.CharField(max_length=64)
    output_sha256 = models.CharField(max_length=64)
    sample = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['group', 'name'], name='storage_case_name_unique')]


class ProblemRelease(models.Model):
    problem = models.OneToOneField('judge.Problem', on_delete=models.CASCADE, related_name='storage_release')
    version = models.ForeignKey(ProblemVersion, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)


class SubmissionVersion(models.Model):
    submission = models.OneToOneField('judge.Submission', on_delete=models.CASCADE, related_name='storage_pin')
    version = models.ForeignKey(ProblemVersion, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
