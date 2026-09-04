from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0008_discoverypreference_notify_new_releases'),
    ]

    operations = [
        migrations.AddField(
            model_name='discoverypreference',
            name='content_mix',
            field=models.CharField(
                choices=[
                    ('balanced', 'Balanced'),
                    ('tv_first', 'TV first'),
                    ('movies_first', 'Movies first'),
                ],
                default='balanced',
                max_length=20,
            ),
        ),
    ]
