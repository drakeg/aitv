from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0011_epg_domain_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChannelFavorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorited_by', to='content.channel')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channel_favorites', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['channel__name'],
                'constraints': [
                    models.UniqueConstraint(fields=('user', 'channel'), name='unique_user_channel_favorite'),
                ],
            },
        ),
    ]
