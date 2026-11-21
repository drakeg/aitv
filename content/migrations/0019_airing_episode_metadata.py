from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0018_alter_airing_id_alter_airingdestination_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='airing',
            name='episode_title',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='airing',
            name='season_number',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='airing',
            name='episode_number',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
