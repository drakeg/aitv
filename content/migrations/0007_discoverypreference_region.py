from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0006_remove_legacy_demo_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='discoverypreference',
            name='region',
            field=models.CharField(default='US', max_length=2),
        ),
        migrations.AddField(
            model_name='discoverypreference',
            name='require_region_availability',
            field=models.BooleanField(default=True),
        ),
    ]
