
from django.db import models

class SystemSettings(models.Model):
    scheduler_type = models.CharField(max_length=10, default="cron")
    enable_notifications = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
