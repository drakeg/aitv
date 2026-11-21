from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_systemsettings_guest_branding'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsettings',
            name='default_region',
            field=models.CharField(
                choices=[
                    ('US', 'United States'),
                    ('CA', 'Canada'),
                    ('GB', 'United Kingdom'),
                    ('AU', 'Australia'),
                    ('DE', 'Germany'),
                    ('FR', 'France'),
                    ('ES', 'Spain'),
                    ('IT', 'Italy'),
                    ('JP', 'Japan'),
                ],
                default='US',
                help_text='Default discovery and Live TV region for guests who are not signed in.',
                max_length=2,
            ),
        ),
    ]
