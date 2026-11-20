from urllib.parse import urlparse

from django import forms
from django.utils import timezone
from django.contrib import admin, messages

from core.epg_health import configured_epg_health, evaluate_epg_state

from .models import (
    Airing,
    AiringDestination,
    Channel,
    ChannelDestination,
    ChannelFavorite,
    ContentAvailability,
    ContentItem,
    EpgRefreshState,
    Program,
)


def _age_label(timestamp, *, now=None):
    if timestamp is None:
        return 'Never'

    now = now or timezone.now()
    seconds = max(0, int((now - timestamp).total_seconds()))
    if seconds < 60:
        return '<1 min ago'

    minutes = seconds // 60
    if minutes < 60:
        return f'{minutes} min ago'

    hours = minutes // 60
    if hours < 48:
        return f'{hours} hr ago'

    days = hours // 24
    return f'{days} days ago'


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


class ChannelDestinationAdminForm(forms.ModelForm):
    class Meta:
        model = ChannelDestination
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data.get('url')
        destination_type = cleaned_data.get('destination_type')
        if (
            url
            and destination_type in {
                ChannelDestination.DestinationType.DIRECT,
                ChannelDestination.DestinationType.TUNER,
            }
        ):
            parsed = urlparse(url)
            if parsed.scheme not in {'http', 'https'}:
                self.add_error('url', 'Playable channel destinations must use http or https.')
        return cleaned_data


class ChannelDestinationInline(admin.TabularInline):
    model = ChannelDestination
    form = ChannelDestinationAdminForm
    extra = 0
    fields = ('provider', 'url', 'access_type', 'destination_type', 'source')
    show_change_link = True


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'source', 'external_id', 'destination_count')
    list_filter = ('region', 'source')
    search_fields = ('name', 'external_id')
    readonly_fields = ('name', 'slug', 'region', 'source', 'external_id', 'logo_url', 'categories')
    inlines = (ChannelDestinationInline,)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Destinations')
    def destination_count(self, obj):
        return obj.destinations.count()


@admin.register(ChannelDestination)
class ChannelDestinationAdmin(admin.ModelAdmin):
    form = ChannelDestinationAdminForm
    list_display = ('channel', 'provider', 'destination_type', 'access_type', 'source')
    list_filter = ('destination_type', 'access_type', 'source')
    search_fields = ('channel__name', 'provider', 'url', 'source')
    autocomplete_fields = ('channel',)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'program_type', 'source', 'external_id')
    list_filter = ('program_type', 'source')
    search_fields = ('title', 'external_id')
    readonly_fields = ('title', 'source', 'external_id', 'description', 'program_type')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Airing)
class AiringAdmin(admin.ModelAdmin):
    list_display = ('channel', 'program', 'starts_at', 'ends_at', 'source')
    list_filter = ('source', 'channel__region')
    search_fields = ('channel__name', 'program__title', 'external_id')
    readonly_fields = ('channel', 'program', 'starts_at', 'ends_at', 'source', 'external_id')
    date_hierarchy = 'starts_at'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AiringDestination)
class AiringDestinationAdmin(admin.ModelAdmin):
    list_display = ('airing', 'provider', 'scope', 'access_type', 'source')
    list_filter = ('scope', 'access_type', 'source')
    search_fields = ('airing__channel__name', 'airing__program__title', 'provider', 'url')
    readonly_fields = ('airing', 'provider', 'url', 'access_type', 'scope', 'source')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(EpgRefreshState)
class EpgRefreshStateAdmin(admin.ModelAdmin):
    list_display = (
        'source',
        'region',
        'health_status',
        'status',
        'attempt_age',
        'success_age',
        'airing_count',
    )
    list_filter = ('source', 'region', 'status')
    readonly_fields = (
        'source',
        'region',
        'health_status',
        'status',
        'attempt_age',
        'success_age',
        'attempted_at',
        'refreshed_at',
        'airing_count',
        'last_error',
    )
    fieldsets = (
        ('Source', {'fields': ('source', 'region')}),
        (
            'Refresh diagnostics',
            {
                'fields': (
                    'health_status',
                    'status',
                    'attempt_age',
                    'success_age',
                    'attempted_at',
                    'refreshed_at',
                    'airing_count',
                ),
            },
        ),
        ('Operator-only failure detail', {'fields': ('last_error',)}),
    )

    @admin.display(description='Health')
    def health_status(self, obj):
        return evaluate_epg_state(obj, now=timezone.now()).upper()

    @admin.display(description='Attempt age')
    def attempt_age(self, obj):
        return _age_label(obj.attempted_at)

    @admin.display(description='Success age')
    def success_age(self, obj):
        return _age_label(obj.refreshed_at)

    def changelist_view(self, request, extra_context=None):
        degraded = [
            f'{region} {health}'
            for region, _state, health in configured_epg_health()
            if health != 'ok'
        ]
        if degraded:
            messages.warning(
                request,
                'EPG diagnostics: ' + ', '.join(degraded) + '.',
            )
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChannelFavorite)
class ChannelFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'created_at')
    list_filter = ('channel__region',)
    search_fields = ('user__username', 'channel__name')
    readonly_fields = ('user', 'channel', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
