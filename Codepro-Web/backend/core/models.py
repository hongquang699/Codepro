# Core application settings and base models
from django.db import models

class SystemConfiguration(models.Model):
    key = models.CharField(max_length=64, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key
