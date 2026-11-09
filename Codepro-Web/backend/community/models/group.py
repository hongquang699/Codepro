from django.db import models
from backend.judge.models import Profile

class Group(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True)
    description = models.TextField(blank=True, default='')
    avatar_url = models.CharField(max_length=255, blank=True, default='')
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='owned_groups')
    is_private = models.BooleanField(default=False)
    member_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class GroupMember(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
        ('member', 'Member'),
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user.user.username} in {self.group.name} ({self.role})"
