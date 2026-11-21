from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_systemsettings_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsettings',
            name='site_name',
            field=models.CharField(
                default='aitv',
                help_text='Guest-facing site or property name.',
                max_length=80,
            ),
        ),
        migrations.AddField(
            model_name='systemsettings',
            name='welcome_message',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Optional guest-facing welcome text shown on the discovery page.',
                max_length=240,
            ),
        ),
    ]
