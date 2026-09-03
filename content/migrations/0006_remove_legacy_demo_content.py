from django.db import migrations


DEMO_URLS = (
    'https://archive.org/details/night_of_the_living_dead',
    'https://archive.org/details/his_girl_friday',
    'https://www.cbs.com/shows/survivor/',
    'https://www.pbs.org/show/frontline/',
    'https://www.fox.com/the-masked-singer/',
    'https://www.themoviedb.org/tv/1396',
    'https://www.themoviedb.org/tv/63639',
    'https://www.youtube.com/watch?v=aqz-KE-bpKQ',
    'https://www.youtube.com/watch?v=eRsGyueVLvQ',
)


def remove_legacy_demo_content(apps, schema_editor):
    ContentItem = apps.get_model('content', 'ContentItem')
    ContentItem.objects.filter(url__in=DEMO_URLS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0005_discoverypreference'),
    ]

    operations = [
        migrations.RunPython(remove_legacy_demo_content, migrations.RunPython.noop),
    ]
