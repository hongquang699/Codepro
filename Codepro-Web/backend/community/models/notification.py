from django.db import models
from backend.judge.models import Profile

class Notification(models.Model):
    TYPE_CHOICES = (
        ('comment', 'Comment'),
        ('reply', 'Reply'),
        ('reaction', 'Reaction'),
        ('mention', 'Mention'),
        ('follow', 'Follow'),
        ('message', 'Message'),
        ('moderation', 'Moderation'),
        ('system', 'System'),
    )
    recipient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='community_notifications')
    sender = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='triggered_notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, default='')
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.user.username}: {self.title}"
