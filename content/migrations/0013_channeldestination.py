from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0012_channelfavorite'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChannelDestination',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(max_length=100)),
                ('url', models.URLField()),
                ('access_type', models.CharField(
                    choices=[
                        ('subscription', 'Subscription'),
                        ('free', 'Free'),
                        ('ads', 'Free with ads'),
                        ('rent', 'Rent'),
                        ('buy', 'Buy'),
                        ('auth', 'TV provider sign-in required'),
                        ('other', 'Other'),
                    ],
                    default='other',
                    max_length=20,
                )),
                ('destination_type', models.CharField(
                    choices=[
                        ('direct', 'Direct playback'),
                        ('provider', 'Provider discovery'),
                        ('details', 'Details'),
                        ('tuner', 'User-owned tuner'),
                    ],
                    default='details',
                    max_length=20,
                )),
                ('source', models.CharField(max_length=50)),
                ('channel', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='destinations',
                    to='content.channel',
                )),
            ],
            options={
                'ordering': ['provider', 'destination_type', 'url'],
                'constraints': [
                    models.UniqueConstraint(
                        fields=('channel', 'source', 'url'),
                        name='unique_channel_destination_source_url',
                    ),
                ],
            },
        ),
    ]
