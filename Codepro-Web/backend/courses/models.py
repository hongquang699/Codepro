from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='authored_courses')
    difficulty = models.CharField(max_length=20, default='Beginner', choices=[
        ('Beginner', 'Nhập môn'),
        ('Intermediate', 'Trung cấp'),
        ('Advanced', 'Nâng cao'),
        ('Expert', 'Chuyên sâu')
    ])
    thumbnail = models.CharField(max_length=255, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class CourseEnrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='students')
    progress_percentage = models.FloatField(default=0.0)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'course')
