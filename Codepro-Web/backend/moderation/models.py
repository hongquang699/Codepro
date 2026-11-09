from django.db import models
from django.contrib.auth.models import User

class ModerationReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_filed')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received', null=True, blank=True)
    reason = models.CharField(max_length=128)
    details = models.TextField()
    status = models.CharField(max_length=32, default='pending', choices=[
        ('pending', 'Chờ xử lý'),
        ('investigating', 'Đang điều tra'),
        ('resolved', 'Đã xử lý'),
        ('dismissed', 'Đã bác bỏ')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report #{self.id}: {self.reason}"
