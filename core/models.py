
from django.db import models

from .regions import REGION_CHOICES

class SystemSettings(models.Model):
    scheduler_type = models.CharField(max_length=10, default="cron")
    enable_notifications = models.BooleanField(default=True)
    site_name = models.CharField(
        max_length=80,
        default="aitv",
        help_text="Guest-facing site or property name.",
    )
    welcome_message = models.CharField(
        max_length=240,
        blank=True,
        default="",
        help_text="Optional guest-facing welcome text shown on the discovery page.",
    )
    default_region = models.CharField(
        max_length=2,
        choices=REGION_CHOICES,
        default="US",
        help_text="Default discovery and Live TV region for guests who are not signed in.",
    )
    show_guest_account_links = models.BooleanField(
        default=True,
        help_text="Show Login and Register actions to anonymous guests.",
    )

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
