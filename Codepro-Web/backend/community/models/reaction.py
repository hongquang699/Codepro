from django.db import models
from backend.judge.models import Profile

class Reaction(models.Model):
    TARGET_TYPE_CHOICES = (
        ('post', 'Post'),
        ('comment', 'Comment'),
        ('thread', 'Thread'),
        ('thread_post', 'Thread Post')
    )
    REACTION_TYPE_CHOICES = (
        ('like', 'Like'),
        ('heart', 'Heart'),
        ('upvote', 'Upvote'),
        ('funny', 'Funny'),
        ('clap', 'Clap'),
    )

    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reactions')
    target_type = models.CharField(max_length=20, choices=TARGET_TYPE_CHOICES)
    target_id = models.PositiveIntegerField(db_index=True)
    reaction_type = models.CharField(max_length=20, choices=REACTION_TYPE_CHOICES, default='like')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'target_type', 'target_id', 'reaction_type')
        indexes = [
            models.Index(fields=['target_type', 'target_id']),
        ]

    def __str__(self):
        return f"{self.user.user.username} {self.reaction_type} on {self.target_type} #{self.target_id}"
