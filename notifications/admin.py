from django.contrib import admin

from .models import ReleaseNotification, ReleaseWatchState

admin.site.register(ReleaseNotification)
admin.site.register(ReleaseWatchState)
