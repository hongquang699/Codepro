from django.db import models
from django.contrib.auth.models import User
from backend.judge.models import Organization, Contest, Problem, Profile

class OrganizationRole(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_roles')
    name = models.CharField(max_length=64)
    color = models.CharField(max_length=32, default='#3b82f6')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organization_roles'

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

class OrganizationPermission(models.Model):
    role = models.ForeignKey(OrganizationRole, on_delete=models.CASCADE, related_name='permissions')
    permission = models.CharField(max_length=64)

    class Meta:
        db_table = 'organization_permissions'

    def __str__(self):
        return f"{self.role.name}: {self.permission}"

class OrganizationMember(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='org_memberships')
    role = models.ForeignKey(OrganizationRole, on_delete=models.RESTRICT, related_name='members')
    status = models.CharField(max_length=32, default='active') # active, pending, banned
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organization_members'
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.organization.short_name or self.organization.name}"

class OrganizationContest(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_contests')
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='org_contests')
    is_official = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organization_contests'
        unique_together = ('organization', 'contest')

    def __str__(self):
        return f"{self.contest.key} @ {self.organization.slug}"

class OrganizationProblem(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_problems')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='org_problems')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organization_problems'
        unique_together = ('organization', 'problem')

    def __str__(self):
        return f"{self.problem.code} @ {self.organization.slug}"

class OrganizationPost(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='org_posts')
    title = models.CharField(max_length=255)
    content = models.TextField()
    summary = models.CharField(max_length=500, blank=True, default='')
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organization_posts'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"[{self.organization.slug}] {self.title}"

class OrganizationAnnouncement(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_announcements')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='org_announcements')
    title = models.CharField(max_length=255)
    content = models.TextField()
    badge_type = models.CharField(max_length=32, default='info') # info, warning, success, danger
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organization_announcements'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.organization.slug}] {self.title}"

class OrganizationActivity(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_activities')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='org_activities')
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=32, blank=True, default='')
    target_id = models.CharField(max_length=64, blank=True, default='')
    target_title = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organization_activity'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.action}"

class OrganizationAuditLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_audit_logs')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='org_audit_logs')
    action = models.CharField(max_length=64)
    target = models.CharField(max_length=128, blank=True, default='')
    ip = models.CharField(max_length=45, default='127.0.0.1')
    details = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organization_audit_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor.username if self.actor else 'System'} - {self.action} on {self.target}"

class OrganizationInvitation(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='org_invitations')
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_org_invitations')
    invitee_username = models.CharField(max_length=150)
    email = models.CharField(max_length=254, blank=True, default='')
    role = models.ForeignKey(OrganizationRole, on_delete=models.CASCADE, related_name='invitations')
    status = models.CharField(max_length=32, default='pending') # pending, accepted, declined, expired
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organization_invitations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Invite {self.invitee_username} to {self.organization.name}"
