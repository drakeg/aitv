from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0009_discoverypreference_content_mix'),
    ]

    operations = [
        migrations.AddField(
            model_name='discoverypreference',
            name='preferred_providers',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
