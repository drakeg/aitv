from content.models import ContentAvailability, ContentItem
from django.core.management.base import BaseCommand


DEMO_ITEMS = [
    {
        'title': 'Night of the Living Dead',
        'url': 'https://archive.org/details/night_of_the_living_dead',
        'genre': 'Horror',
        'duration': 96,
        'source_type': 'internet_archive',
        'content_type': 'movie',
        'description': 'Classic public-domain horror film available from the Internet Archive.',
        'release_year': 1968,
        'availability': {
            'provider': 'Internet Archive',
            'url': 'https://archive.org/details/night_of_the_living_dead',
            'access_type': 'free',
        },
    },
    {
        'title': 'His Girl Friday',
        'url': 'https://archive.org/details/his_girl_friday',
        'genre': 'Comedy, Romance',
        'duration': 92,
        'source_type': 'internet_archive',
        'content_type': 'movie',
        'description': 'Classic screwball comedy represented as a free movie source.',
        'release_year': 1940,
        'availability': {
            'provider': 'Internet Archive',
            'url': 'https://archive.org/details/his_girl_friday',
            'access_type': 'free',
        },
    },
    {
        'title': 'Survivor',
        'url': 'https://www.cbs.com/shows/survivor/',
        'genre': 'Reality',
        'source_type': 'network',
        'content_type': 'tv',
        'description': 'CBS series page with current seasons and full-episode access where available.',
        'release_year': 2000,
        'availability': {
            'provider': 'CBS',
            'url': 'https://www.cbs.com/shows/survivor/',
            'access_type': 'other',
        },
    },
    {
        'title': 'FRONTLINE',
        'url': 'https://www.pbs.org/show/frontline/',
        'genre': 'Documentary, News',
        'source_type': 'network',
        'content_type': 'tv',
        'description': 'PBS investigative journalism with episodes and specials available from PBS.',
        'release_year': 1983,
        'availability': {
            'provider': 'PBS',
            'url': 'https://www.pbs.org/show/frontline/',
            'access_type': 'free',
        },
    },
    {
        'title': 'The Masked Singer',
        'url': 'https://www.fox.com/the-masked-singer/',
        'genre': 'Reality, Music',
        'source_type': 'network',
        'content_type': 'tv',
        'description': 'FOX series page with direct network watch access where available.',
        'release_year': 2019,
        'availability': {
            'provider': 'FOX',
            'url': 'https://www.fox.com/the-masked-singer/',
            'access_type': 'other',
        },
    },
    {
        'title': 'Breaking Bad',
        'url': 'https://www.themoviedb.org/tv/1396',
        'genre': 'Crime, Drama',
        'source_type': 'tmdb',
        'content_type': 'tv',
        'description': 'Metadata/discovery example; a direct provider can be attached separately.',
        'release_year': 2008,
        'external_source': 'tmdb',
        'external_id': '1396',
    },
    {
        'title': 'The Expanse',
        'url': 'https://www.themoviedb.org/tv/63639',
        'genre': 'Drama, Science Fiction',
        'source_type': 'tmdb',
        'content_type': 'tv',
        'description': 'Metadata/discovery example; a direct provider can be attached separately.',
        'release_year': 2015,
        'external_source': 'tmdb',
        'external_id': '63639',
    },
    {
        'title': 'Big Buck Bunny',
        'url': 'https://www.youtube.com/watch?v=aqz-KE-bpKQ',
        'genre': 'Comedy, Animation',
        'duration': 10,
        'thumbnail': 'https://img.youtube.com/vi/aqz-KE-bpKQ/hqdefault.jpg',
        'source_type': 'youtube',
        'content_type': 'video',
        'availability': {
            'provider': 'YouTube',
            'url': 'https://www.youtube.com/watch?v=aqz-KE-bpKQ',
            'access_type': 'free',
        },
    },
    {
        'title': 'Sintel',
        'url': 'https://www.youtube.com/watch?v=eRsGyueVLvQ',
        'genre': 'Action, Animation',
        'duration': 15,
        'thumbnail': 'https://img.youtube.com/vi/eRsGyueVLvQ/hqdefault.jpg',
        'source_type': 'youtube',
        'content_type': 'video',
        'availability': {
            'provider': 'YouTube',
            'url': 'https://www.youtube.com/watch?v=eRsGyueVLvQ',
            'access_type': 'free',
        },
    },
]


class Command(BaseCommand):
    help = 'Create an idempotent multi-source demo catalog for local development.'

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for demo in DEMO_ITEMS:
            item_data = demo.copy()
            availability = item_data.pop('availability', None)
            item, was_created = ContentItem.objects.update_or_create(
                url=item_data['url'],
                defaults=item_data,
            )
            if availability:
                ContentAvailability.objects.update_or_create(
                    content=item,
                    provider=availability['provider'],
                    url=availability['url'],
                    defaults={'access_type': availability['access_type']},
                )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Demo content ready: {created} created, {updated} refreshed.'
            )
        )
