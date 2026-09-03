from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0007_discoverypreference_region'),
    ]

    operations = [
        migrations.AddField(
            model_name='discoverypreference',
            name='notify_new_releases',
            field=models.BooleanField(default=False),
        ),
    ]
