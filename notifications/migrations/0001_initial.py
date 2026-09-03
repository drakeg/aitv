from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0008_discoverypreference_notify_new_releases'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReleaseWatchState',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_event_key', models.CharField(blank=True, max_length=255)),
                ('checked_at', models.DateTimeField(auto_now=True)),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='content.contentitem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ReleaseNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_key', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('target_url', models.URLField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='content.contentitem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AddConstraint(
            model_name='releasewatchstate',
            constraint=models.UniqueConstraint(fields=('user', 'content'), name='unique_release_watch_state'),
        ),
        migrations.AddConstraint(
            model_name='releasenotification',
            constraint=models.UniqueConstraint(fields=('user', 'content', 'event_key'), name='unique_release_notification_event'),
        ),
    ]
