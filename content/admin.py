from django.contrib import admin

from .models import ContentAvailability, ContentItem


@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_type', 'source_type', 'release_year', 'rating')
    list_filter = ('content_type', 'source_type')
    search_fields = ('title', 'genre', 'external_id')


@admin.register(ContentAvailability)
class ContentAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('content', 'provider', 'access_type')
    list_filter = ('provider', 'access_type')
    search_fields = ('content__title', 'provider')
