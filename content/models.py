from django.conf import settings
from django.db import models


class ContentItem(models.Model):
    class ContentType(models.TextChoices):
        MOVIE = 'movie', 'Movie'
        TV = 'tv', 'TV Show'
        VIDEO = 'video', 'Video'

    title = models.CharField(max_length=255)
    url = models.URLField()
    genre = models.CharField(max_length=100)
    duration = models.IntegerField(null=True, blank=True)
    thumbnail = models.URLField(blank=True, null=True)
    source_type = models.CharField(max_length=20)
    content_type = models.CharField(max_length=10, choices=ContentType.choices, default=ContentType.VIDEO)
    description = models.TextField(blank=True)
    release_year = models.PositiveSmallIntegerField(null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    external_source = models.CharField(max_length=30, blank=True)
    external_id = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.title


class ContentAvailability(models.Model):
    class AccessType(models.TextChoices):
        SUBSCRIPTION = 'subscription', 'Subscription'
        FREE = 'free', 'Free'
        ADS = 'ads', 'Free with ads'
        RENT = 'rent', 'Rent'
        BUY = 'buy', 'Buy'
        AUTH = 'auth', 'TV provider sign-in required'
        OTHER = 'other', 'Other'

    content = models.ForeignKey(ContentItem, on_delete=models.CASCADE, related_name='availabilities')
    provider = models.CharField(max_length=100)
    url = models.URLField()
    access_type = models.CharField(max_length=20, choices=AccessType.choices, default=AccessType.OTHER)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['content', 'provider', 'url'], name='unique_content_provider_url')]
        ordering = ['provider']

    @property
    def action_label(self):
        if self.access_type in {self.AccessType.FREE, self.AccessType.ADS}:
            return f'Watch on {self.provider}'
        if self.access_type == self.AccessType.AUTH:
            return f'{self.provider} · Sign-in required'
        if self.access_type == self.AccessType.SUBSCRIPTION:
            return f'{self.provider} · Subscription'
        if self.access_type == self.AccessType.RENT:
            return f'Rent on {self.provider}'
        if self.access_type == self.AccessType.BUY:
            return f'Buy on {self.provider}'
        return f'Open {self.provider}'

    def __str__(self):
        return f'{self.content}: {self.provider}'


class DiscoveryPreference(models.Model):
    class ContentMix(models.TextChoices):
        BALANCED = 'balanced', 'Balanced'
        TV_FIRST = 'tv_first', 'TV first'
        MOVIES_FIRST = 'movies_first', 'Movies first'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='discovery_preference')
    preferred_genres = models.JSONField(default=list, blank=True)
    preferred_providers = models.JSONField(default=list, blank=True)
    customized = models.BooleanField(default=False)
    region = models.CharField(max_length=2, default='US')
    require_region_availability = models.BooleanField(default=True)
    notify_new_releases = models.BooleanField(default=False)
    content_mix = models.CharField(max_length=20, choices=ContentMix.choices, default=ContentMix.BALANCED)

    def __str__(self):
        return f'Discovery preferences for {self.user}'


class Channel(models.Model):
    """Normalized Live TV channel identity independent of schedule/playback."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    region = models.CharField(max_length=2, default='US')
    source = models.CharField(max_length=50)
    external_id = models.CharField(max_length=100)
    logo_url = models.URLField(blank=True)
    categories = models.JSONField(default=list, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id', 'region'],
                name='unique_channel_source_external_region',
            ),
        ]
        ordering = ['name', 'region']

    def __str__(self):
        return self.name


class ChannelDestination(models.Model):
    """Trusted channel destination kept separate from schedule metadata."""

    class DestinationType(models.TextChoices):
        DIRECT = 'direct', 'Direct playback'
        PROVIDER = 'provider', 'Provider discovery'
        DETAILS = 'details', 'Details'
        TUNER = 'tuner', 'User-owned tuner'

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='destinations')
    provider = models.CharField(max_length=100)
    url = models.URLField()
    access_type = models.CharField(
        max_length=20,
        choices=ContentAvailability.AccessType.choices,
        default=ContentAvailability.AccessType.OTHER,
    )
    destination_type = models.CharField(
        max_length=20,
        choices=DestinationType.choices,
        default=DestinationType.DETAILS,
    )
    source = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['channel', 'source', 'url'],
                name='unique_channel_destination_source_url',
            ),
        ]
        ordering = ['provider', 'destination_type', 'url']

    @property
    def is_playable(self):
        return self.destination_type in {self.DestinationType.DIRECT, self.DestinationType.TUNER}

    @property
    def action_label(self):
        if self.destination_type == self.DestinationType.TUNER:
            return f'Watch via {self.provider}'
        if self.destination_type != self.DestinationType.DIRECT:
            return f'Open {self.provider}'
        if self.access_type == ContentAvailability.AccessType.AUTH:
            return f'{self.provider} · Sign-in required'
        if self.access_type == ContentAvailability.AccessType.SUBSCRIPTION:
            return f'{self.provider} · Subscription'
        if self.access_type in {
            ContentAvailability.AccessType.FREE,
            ContentAvailability.AccessType.ADS,
        }:
            return f'Watch on {self.provider}'
        return f'Watch on {self.provider}'

    def __str__(self):
        return f'{self.channel}: {self.provider}'


class AiringDestination(models.Model):
    """Trusted destination for one scheduled airing, separate from channel playback."""

    class Scope(models.TextChoices):
        EPISODE = 'episode', 'Episode'
        SHOW = 'show', 'Show'

    airing = models.ForeignKey('Airing', on_delete=models.CASCADE, related_name='destinations')
    provider = models.CharField(max_length=100)
    url = models.URLField()
    access_type = models.CharField(
        max_length=20,
        choices=ContentAvailability.AccessType.choices,
        default=ContentAvailability.AccessType.OTHER,
    )
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.SHOW)
    source = models.CharField(max_length=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['airing', 'source', 'url'],
                name='unique_airing_destination_source_url',
            ),
        ]
        ordering = ['provider', 'scope', 'url']

    @property
    def action_label(self):
        if self.access_type == ContentAvailability.AccessType.AUTH:
            return f'{self.provider} · Sign-in required'
        if self.access_type == ContentAvailability.AccessType.SUBSCRIPTION:
            return f'{self.provider} · Subscription'
        if self.access_type in {
            ContentAvailability.AccessType.FREE,
            ContentAvailability.AccessType.ADS,
        }:
            return f'Watch on {self.provider}'
        return f'Watch on {self.provider}'

    def __str__(self):
        return f'{self.airing}: {self.provider}'


class ChannelFavorite(models.Model):
    """Per-account saved channel preference for the Live TV guide."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='channel_favorites')
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'channel'],
                name='unique_user_channel_favorite',
            ),
        ]
        ordering = ['channel__name']

    def __str__(self):
        return f'{self.user}: {self.channel}'


class Program(models.Model):
    """Program metadata that can be reused across multiple channel airings."""

    title = models.CharField(max_length=255)
    source = models.CharField(max_length=50)
    external_id = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    program_type = models.CharField(max_length=50, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                name='unique_program_source_external',
            ),
        ]
        ordering = ['title']

    def __str__(self):
        return self.title


class Airing(models.Model):
    """A scheduled program occurrence; schedule data does not imply playback."""

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='airings')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='airings')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    source = models.CharField(max_length=50)
    external_id = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'external_id'],
                name='unique_airing_source_external',
            ),
            models.CheckConstraint(
                condition=models.Q(ends_at__gt=models.F('starts_at')),
                name='airing_ends_after_start',
            ),
        ]
        ordering = ['starts_at', 'channel__name']

    def __str__(self):
        return f'{self.channel}: {self.program} @ {self.starts_at}'
