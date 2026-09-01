
from django.db import models
from django.contrib.auth.models import User

class NotificationPreference(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    genre = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=10, default="daily")
