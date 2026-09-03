from urllib.parse import urlparse

from .models import ContentAvailability


PROVIDER_RULES = (
    {
        'domains': ('abc.com',),
        'provider': 'ABC',
        'source_type': 'network',
        'access_type': ContentAvailability.AccessType.OTHER,
    },
    {
        'domains': ('cbs.com',),
        'provider': 'CBS',
        'source_type': 'network',
        'access_type': ContentAvailability.AccessType.OTHER,
    },
    {
        'domains': ('nbc.com',),
        'provider': 'NBC',
        'source_type': 'network',
        'access_type': ContentAvailability.AccessType.OTHER,
    },
    {
        'domains': ('fox.com',),
        'provider': 'FOX',
        'source_type': 'network',
        'access_type': ContentAvailability.AccessType.AUTH,
    },
    {
        'domains': ('pbs.org',),
        'provider': 'PBS',
        'source_type': 'network',
        'access_type': ContentAvailability.AccessType.FREE,
    },
    {
        'domains': ('cwtv.com',),
        'provider': 'The CW',
        'source_type': 'network',
        'access_type': ContentAvailability.AccessType.ADS,
    },
    {
        'domains': ('youtube.com', 'youtu.be'),
        'provider': 'YouTube',
        'source_type': 'youtube',
        'access_type': ContentAvailability.AccessType.FREE,
    },
    {
        'domains': ('archive.org',),
        'provider': 'Internet Archive',
        'source_type': 'internet_archive',
        'access_type': ContentAvailability.AccessType.FREE,
    },
    {
        'domains': ('tubitv.com',),
        'provider': 'Tubi',
        'source_type': 'streaming',
        'access_type': ContentAvailability.AccessType.ADS,
    },
    {
        'domains': ('pluto.tv',),
        'provider': 'Pluto TV',
        'source_type': 'streaming',
        'access_type': ContentAvailability.AccessType.ADS,
    },
    {
        'domains': ('paramountplus.com',),
        'provider': 'Paramount+',
        'source_type': 'streaming',
        'access_type': ContentAvailability.AccessType.SUBSCRIPTION,
    },
    {
        'domains': ('peacocktv.com',),
        'provider': 'Peacock',
        'source_type': 'streaming',
        'access_type': ContentAvailability.AccessType.SUBSCRIPTION,
    },
    {
        'domains': ('hulu.com',),
        'provider': 'Hulu',
        'source_type': 'streaming',
        'access_type': ContentAvailability.AccessType.SUBSCRIPTION,
    },
    {
        'domains': ('disneyplus.com',),
        'provider': 'Disney+',
        'source_type': 'streaming',
        'access_type': ContentAvailability.AccessType.SUBSCRIPTION,
    },
    {
        'domains': ('max.com',),
        'provider': 'Max',
        'source_type': 'streaming',
        'access_type': ContentAvailability.AccessType.SUBSCRIPTION,
    },
    {
        'domains': ('netflix.com',),
        'provider': 'Netflix',
        'source_type': 'streaming',
        'access_type': ContentAvailability.AccessType.SUBSCRIPTION,
    },
    {
        'domains': ('primevideo.com',),
        'provider': 'Prime Video',
        'source_type': 'streaming',
        'access_type': ContentAvailability.AccessType.SUBSCRIPTION,
    },
    {
        'domains': ('tv.apple.com',),
        'provider': 'Apple TV',
        'source_type': 'streaming',
        'access_type': ContentAvailability.AccessType.OTHER,
    },
    {
        'domains': ('plex.tv',),
        'provider': 'Plex',
        'source_type': 'streaming',
        'access_type': ContentAvailability.AccessType.OTHER,
    },
)

NETWORK_PROVIDERS = frozenset({'ABC', 'CBS', 'NBC', 'FOX', 'PBS', 'The CW'})


def _host_matches(host, domain):
    return host == domain or host.endswith(f'.{domain}')


def detect_provider(url):
    """Return provider metadata for a known direct-watch URL, if recognized."""
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'}:
        return None

    host = (parsed.hostname or '').lower()
    for rule in PROVIDER_RULES:
        if any(_host_matches(host, domain) for domain in rule['domains']):
            return rule
    return None


def ensure_direct_availability(item):
    """Create/update an availability record when an item's URL is a known provider."""
    provider = detect_provider(item.url)
    if not provider:
        return None

    availability, _ = ContentAvailability.objects.update_or_create(
        content=item,
        provider=provider['provider'],
        url=item.url,
        defaults={'access_type': provider['access_type']},
    )
    return availability
