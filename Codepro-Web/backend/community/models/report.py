from django.db import models
from backend.judge.models import Profile

class Report(models.Model):
    TARGET_TYPE_CHOICES = (
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('thread', 'Thread'),
        ('thread_post', 'Thread Post'),
        ('user', 'User')
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
        ('actioned', 'Actioned')
    )
    reporter = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reports_submitted')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES)
    target_id = models.PositiveIntegerField()
    reason = models.CharField(max_length=255)
    details = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    resolved_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_resolved')
    resolution_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{self.id} on {self.target_type} #{self.target_id} ({self.status})"

class ModerationAction(models.Model):
    ACTION_CHOICES = (
        ('hide', 'Hide'),
        ('restore', 'Restore'),
        ('lock', 'Lock'),
        ('pin', 'Pin'),
        ('delete', 'Delete'),
        ('ban', 'Ban User'),
    )
    moderator = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='moderation_actions')
    target_type = models.CharField(max_length=20)
    target_id = models.PositiveIntegerField()
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.moderator.user.username} {self.action} on {self.target_type} #{self.target_id}"
