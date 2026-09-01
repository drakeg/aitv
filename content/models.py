
from django.db import models

class ContentItem(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    genre = models.CharField(max_length=100)
    duration = models.IntegerField(null=True, blank=True)
    thumbnail = models.URLField(blank=True, null=True)
    source_type = models.CharField(max_length=20)

    def __str__(self):
        return self.title
