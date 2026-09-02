from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0003_contentitem_thumbnail'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentitem',
            name='content_type',
            field=models.CharField(
                choices=[('movie', 'Movie'), ('tv', 'TV Show'), ('video', 'Video')],
                default='video',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='contentitem',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='contentitem',
            name='external_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='contentitem',
            name='external_source',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='contentitem',
            name='rating',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True),
        ),
        migrations.AddField(
            model_name='contentitem',
            name='release_year',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='ContentAvailability',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(max_length=100)),
                ('url', models.URLField()),
                ('access_type', models.CharField(choices=[('subscription', 'Subscription'), ('free', 'Free'), ('ads', 'Free with ads'), ('rent', 'Rent'), ('buy', 'Buy'), ('other', 'Other')], default='other', max_length=20)),
                ('content', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='availabilities', to='content.contentitem')),
            ],
            options={
                'ordering': ['provider'],
            },
        ),
        migrations.AddConstraint(
            model_name='contentavailability',
            constraint=models.UniqueConstraint(fields=('content', 'provider', 'url'), name='unique_content_provider_url'),
        ),
    ]
