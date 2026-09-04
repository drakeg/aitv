from django.db import models
from django.contrib.auth.models import User
from content.models import ContentItem


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.ForeignKey(ContentItem, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    is_favorite = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'content')
