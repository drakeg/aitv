from django.conf import settings
from django.db import models

from content.models import ContentItem


class ReleaseWatchState(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.ForeignKey(ContentItem, on_delete=models.CASCADE)
    last_event_key = models.CharField(max_length=255, blank=True)
    checked_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'content'],
                name='unique_release_watch_state',
            )
        ]


class ReleaseNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.ForeignKey(ContentItem, on_delete=models.CASCADE)
    event_key = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    message = models.TextField()
    target_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'content', 'event_key'],
                name='unique_release_notification_event',
            )
        ]

    @property
    def is_read(self):
        return self.read_at is not None
