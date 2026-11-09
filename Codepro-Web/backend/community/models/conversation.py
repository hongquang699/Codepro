from django.db import models
from backend.judge.models import Profile

class Conversation(models.Model):
    participant_1 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='conversations_1')
    participant_2 = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='conversations_2')
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('participant_1', 'participant_2')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Chat: {self.participant_1.user.username} & {self.participant_2.user.username}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.user.username} at {self.created_at}"
