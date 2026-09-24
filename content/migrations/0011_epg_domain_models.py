# Generated for Sprint 57: normalized Live TV / EPG domain foundation.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0010_discoverypreference_preferred_providers'),
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.SlugField(max_length=255)),
                ('region', models.CharField(default='US', max_length=2)),
                ('source', models.CharField(max_length=50)),
                ('external_id', models.CharField(max_length=100)),
                ('logo_url', models.URLField(blank=True)),
                ('categories', models.JSONField(blank=True, default=list)),
            ],
            options={'ordering': ['name', 'region']},
        ),
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('source', models.CharField(max_length=50)),
                ('external_id', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('program_type', models.CharField(blank=True, max_length=50)),
            ],
            options={'ordering': ['title']},
        ),
        migrations.CreateModel(
            name='Airing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('starts_at', models.DateTimeField()),
                ('ends_at', models.DateTimeField()),
                ('source', models.CharField(max_length=50)),
                ('external_id', models.CharField(max_length=100)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='airings', to='content.channel')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='airings', to='content.program')),
            ],
            options={'ordering': ['starts_at', 'channel__name']},
        ),
        migrations.AddConstraint(
            model_name='channel',
            constraint=models.UniqueConstraint(fields=('source', 'external_id', 'region'), name='unique_channel_source_external_region'),
        ),
        migrations.AddConstraint(
            model_name='program',
            constraint=models.UniqueConstraint(fields=('source', 'external_id'), name='unique_program_source_external'),
        ),
        migrations.AddConstraint(
            model_name='airing',
            constraint=models.UniqueConstraint(fields=('source', 'external_id'), name='unique_airing_source_external'),
        ),
        migrations.AddConstraint(
            model_name='airing',
            constraint=models.CheckConstraint(condition=models.Q(('ends_at__gt', models.F('starts_at'))), name='airing_ends_after_start'),
        ),
    ]
