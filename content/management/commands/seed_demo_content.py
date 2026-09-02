from django.core.management.base import BaseCommand

from content.models import ContentItem


DEMO_ITEMS = [
    {
        'title': 'Big Buck Bunny',
        'url': 'https://www.youtube.com/watch?v=aqz-KE-bpKQ',
        'genre': 'Comedy, Animation',
        'duration': 10,
        'thumbnail': 'https://img.youtube.com/vi/aqz-KE-bpKQ/hqdefault.jpg',
        'source_type': 'youtube',
    },
    {
        'title': 'Sintel',
        'url': 'https://www.youtube.com/watch?v=eRsGyueVLvQ',
        'genre': 'Action, Animation',
        'duration': 15,
        'thumbnail': 'https://img.youtube.com/vi/eRsGyueVLvQ/hqdefault.jpg',
        'source_type': 'youtube',
    },
    {
        'title': 'Tears of Steel',
        'url': 'https://www.youtube.com/watch?v=R6MlUcmOul8',
        'genre': 'Action, Science Fiction',
        'duration': 12,
        'thumbnail': 'https://img.youtube.com/vi/R6MlUcmOul8/hqdefault.jpg',
        'source_type': 'youtube',
    },
    {
        'title': 'Elephants Dream',
        'url': 'https://www.youtube.com/watch?v=TLkA0RELQ1g',
        'genre': 'Science Fiction, Animation',
        'duration': 11,
        'thumbnail': 'https://img.youtube.com/vi/TLkA0RELQ1g/hqdefault.jpg',
        'source_type': 'youtube',
    },
]


class Command(BaseCommand):
    help = 'Create a small idempotent demo catalog for local development.'

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for item in DEMO_ITEMS:
            _, was_created = ContentItem.objects.update_or_create(
                url=item['url'],
                defaults=item,
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
