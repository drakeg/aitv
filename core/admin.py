from django.contrib import admin

from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Guest branding', {
            'fields': ('site_name', 'welcome_message', 'default_region'),
        }),
        ('System behavior', {
            'fields': ('scheduler_type', 'enable_notifications'),
        }),
    )

    def has_add_permission(self, request):
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
