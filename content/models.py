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
    content_type = models.CharField(
        max_length=10,
        choices=ContentType.choices,
        default=ContentType.VIDEO,
    )
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
        OTHER = 'other', 'Other'

    content = models.ForeignKey(
        ContentItem,
        on_delete=models.CASCADE,
        related_name='availabilities',
    )
    provider = models.CharField(max_length=100)
    url = models.URLField()
    access_type = models.CharField(
        max_length=20,
        choices=AccessType.choices,
        default=AccessType.OTHER,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['content', 'provider', 'url'],
                name='unique_content_provider_url',
            )
        ]
        ordering = ['provider']

    def __str__(self):
        return f'{self.content}: {self.provider}'
