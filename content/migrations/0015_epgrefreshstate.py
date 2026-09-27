from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0014_airingdestination'),
    ]

    operations = [
        migrations.CreateModel(
            name='EpgRefreshState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(max_length=50)),
                ('region', models.CharField(max_length=2)),
                ('refreshed_at', models.DateTimeField()),
                ('airing_count', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['source', 'region'],
                'constraints': [
                    models.UniqueConstraint(
                        fields=('source', 'region'),
                        name='unique_epg_refresh_state_source_region',
                    ),
                ],
            },
        ),
    ]
