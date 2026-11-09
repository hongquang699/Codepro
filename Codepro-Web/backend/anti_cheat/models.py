from django.conf import settings
from django.db import models


class AntiCheatSettings(models.Model):
    contest = models.OneToOneField('judge.Contest', on_delete=models.CASCADE, related_name='anti_cheat_settings')
    enabled = models.BooleanField(default=True)
    similarity_threshold = models.PositiveSmallIntegerField(default=89)
    scan_mode = models.CharField(max_length=12, choices=[
        ('realtime', 'Realtime'), ('scheduled', 'Scheduled'), ('manual', 'Manual')
    ], default='realtime')
    min_tokens = models.PositiveSmallIntegerField(default=30)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'anti_cheat_settings'


class ScanJob(models.Model):
    contest = models.ForeignKey('judge.Contest', on_delete=models.CASCADE, related_name='anti_cheat_scans')
    target_submission = models.ForeignKey('judge.Submission', on_delete=models.CASCADE, null=True, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=12, choices=[
        ('PENDING', 'Pending'), ('RUNNING', 'Running'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')
    ], default='PENDING', db_index=True)
    processed = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    matches = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'anti_cheat_scan_jobs'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', 'created_at'])]


class SimilarityResult(models.Model):
    contest = models.ForeignKey('judge.Contest', on_delete=models.CASCADE, related_name='anti_cheat_results')
    problem = models.ForeignKey('judge.Problem', on_delete=models.CASCADE)
    submission_a = models.ForeignKey('judge.Submission', on_delete=models.CASCADE, related_name='anti_cheat_matches_a')
    submission_b = models.ForeignKey('judge.Submission', on_delete=models.CASCADE, related_name='anti_cheat_matches_b')
    score = models.FloatField()
    algorithm_version = models.CharField(max_length=32)
    source_a_sha256 = models.CharField(max_length=64)
    source_b_sha256 = models.CharField(max_length=64)
    evidence = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'anti_cheat_similarity_results'
        constraints = [models.UniqueConstraint(fields=['submission_a', 'submission_b'], name='anti_cheat_unique_pair')]
        indexes = [models.Index(fields=['contest', 'score'])]


class AntiCheatCase(models.Model):
    result = models.OneToOneField(SimilarityResult, on_delete=models.CASCADE, related_name='case')
    contest = models.ForeignKey('judge.Contest', on_delete=models.CASCADE, related_name='anti_cheat_cases')
    status = models.CharField(max_length=16, choices=[
        ('OPEN', 'Open'), ('UNDER_REVIEW', 'Under review'), ('CONFIRMED', 'Confirmed'),
        ('DISMISSED', 'Dismissed'), ('APPEALED', 'Appealed'), ('CLOSED', 'Closed')
    ], default='OPEN', db_index=True)
    reason = models.TextField(blank=True, default='')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'anti_cheat_cases'
        ordering = ['-created_at']


class AntiCheatPenalty(models.Model):
    case = models.ForeignKey(AntiCheatCase, on_delete=models.CASCADE, related_name='penalties')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=16, choices=[
        ('WARNING', 'Warning'), ('DISQUALIFY', 'Disqualify from contest')
    ])
    reason = models.TextField()
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'anti_cheat_penalties'
        constraints = [models.UniqueConstraint(fields=['case', 'user', 'kind'], name='anti_cheat_unique_penalty')]


class AntiCheatAppeal(models.Model):
    penalty = models.ForeignKey(AntiCheatPenalty, on_delete=models.CASCADE, related_name='appeals')
    appellant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+')
    reason = models.TextField()
    status = models.CharField(max_length=12, choices=[
        ('OPEN', 'Open'), ('UPHELD', 'Upheld'), ('REJECTED', 'Rejected')
    ], default='OPEN')
    decision = models.TextField(blank=True, default='')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'anti_cheat_appeals'
