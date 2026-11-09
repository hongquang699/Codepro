from django.db import models
from django.contrib.auth.models import User
from backend.judge.models import Contest, Problem, ContestProblem

class ContestAuditLog(models.Model):
    """Audit log recording every significant administrative action in a contest."""
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='audit_logs')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contest_audit_actions')
    action = models.CharField(max_length=64, db_index=True)
    target_type = models.CharField(max_length=64, blank=True, default='')
    target_id = models.CharField(max_length=128, blank=True, default='')
    details = models.TextField(blank=True, default='')
    ip_address = models.CharField(max_length=45, default='127.0.0.1')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'system'
        return f"[{self.contest.key}] {actor_name} -> {self.action} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"


class ContestAdminRole(models.Model):
    """Scoped role assignments for a specific contest."""
    ROLE_CHOICES = (
        ('owner', 'Contest Owner'),
        ('contest_manager', 'Contest Manager'),
        ('problem_setter', 'Problem Setter'),
        ('jury_manager', 'Jury Manager'),
        ('moderator', 'Moderator'),
        ('observer', 'Observer')
    )
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='admin_roles')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contest_admin_roles')
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default='contest_manager')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('contest', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()} ({self.contest.key})"


class ContestAnnouncement(models.Model):
    """Internal official announcements published specifically for a contest."""
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='contest_announcements')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"{self.contest.key} - {self.title}"


class ContestBan(models.Model):
    """Record of banned or disqualified contestants."""
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='contest_bans')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contest_bans')
    reason = models.TextField(blank=True, default='')
    banned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='imposed_bans')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('contest', 'user')

    def __str__(self):
        return f"Banned: {self.user.username} from {self.contest.key}"
