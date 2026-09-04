from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('watchlist', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='watchlist',
            name='is_favorite',
            field=models.BooleanField(default=False),
        ),
    ]
