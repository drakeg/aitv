from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_systemsettings_default_region'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsettings',
            name='show_guest_account_links',
            field=models.BooleanField(
                default=True,
                help_text='Show Login and Register actions to anonymous guests.',
            ),
        ),
    ]
