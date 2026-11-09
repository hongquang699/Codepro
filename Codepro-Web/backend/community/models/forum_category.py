from django.db import models

class ForumCategory(models.Model):
    name = models.CharField(max_length=128)
    slug = models.SlugField(max_length=128, unique=True)
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=64, default='chat')
    order = models.PositiveIntegerField(default=1)
    thread_count = models.PositiveIntegerField(default=0)
    post_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
