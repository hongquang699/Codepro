from django.db import models
from django.contrib.auth.models import User
from backend.judge.models import Profile

class Post(models.Model):
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='community_posts')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField(help_text='Markdown & KaTeX content')
    summary = models.CharField(max_length=500, blank=True, default='')
    tags = models.JSONField(default=list, blank=True)
    is_pinned = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"{self.title} by {self.author.user.username}"
