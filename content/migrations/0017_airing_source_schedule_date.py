from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0016_epgrefreshstate_failure_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='airing',
            name='source_schedule_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
