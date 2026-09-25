from django.core.management.base import BaseCommand, CommandError

from content.services import refresh_tvmaze_epg


class Command(BaseCommand):
    help = 'Refresh normalized Live TV EPG data from configured trusted schedule sources.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--region',
            action='append',
            dest='regions',
            help='Two-letter region code to refresh. Repeat for multiple regions. Defaults to US.',
        )
        parser.add_argument(
            '--regions',
            dest='regions_csv',
            help='Comma-separated two-letter region codes. May be combined with repeated --region options.',
        )
        parser.add_argument(
            '--retention-hours',
            type=int,
            default=6,
            help='Keep expired source airings for this many hours before cleanup. Defaults to 6.',
        )

    def handle(self, *args, **options):
        retention_hours = options['retention_hours']
        if retention_hours < 0:
            raise CommandError('--retention-hours must be zero or greater.')

        raw_regions = list(options.get('regions') or [])
        regions_csv = str(options.get('regions_csv') or '').strip()
        if regions_csv:
            raw_regions.extend(regions_csv.split(','))
        if not raw_regions:
            raw_regions = ['US']

        regions = []
        for value in raw_regions:
            region = str(value or '').strip().upper()
            if len(region) != 2 or not region.isalpha():
                raise CommandError(f'Invalid region "{value}". Use a two-letter code such as US or CA.')
            if region not in regions:
                regions.append(region)

        total = 0
        for region in regions:
            count = refresh_tvmaze_epg(country=region, retention_hours=retention_hours)
            total += count
            self.stdout.write(f'{region}: refreshed {count} airing(s).')

        self.stdout.write(
            self.style.SUCCESS(
                f'Refreshed {total} airing(s) across {len(regions)} region(s).'
            )
        )
