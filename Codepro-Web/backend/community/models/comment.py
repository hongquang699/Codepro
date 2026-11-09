from django.db import models
from backend.judge.models import Profile
from .post import Post

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='community_comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    like_count = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.user.username} on post #{self.post_id}"
