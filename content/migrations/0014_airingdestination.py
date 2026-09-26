from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0013_channeldestination'),
    ]

    operations = [
        migrations.CreateModel(
            name='AiringDestination',
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
                ('scope', models.CharField(
                    choices=[('episode', 'Episode'), ('show', 'Show')],
                    default='show',
                    max_length=20,
                )),
                ('source', models.CharField(max_length=50)),
                ('airing', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='destinations',
                    to='content.airing',
                )),
            ],
            options={
                'ordering': ['provider', 'scope', 'url'],
                'constraints': [
                    models.UniqueConstraint(
                        fields=('airing', 'source', 'url'),
                        name='unique_airing_destination_source_url',
                    ),
                ],
            },
        ),
    ]
