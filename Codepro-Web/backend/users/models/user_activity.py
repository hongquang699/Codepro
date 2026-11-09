from django.db import models
from django.contrib.auth.models import User

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_activities')
    activity_type = models.CharField(max_length=50)  # submission, contest, problem, blog, forum, achievement, organization
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    link = models.CharField(max_length=300, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_activities'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.activity_type}] {self.user.username}: {self.title}"
