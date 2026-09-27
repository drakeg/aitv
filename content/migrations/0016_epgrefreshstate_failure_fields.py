from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0015_epgrefreshstate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='epgrefreshstate',
            name='refreshed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='epgrefreshstate',
            name='attempted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='epgrefreshstate',
            name='status',
            field=models.CharField(
                blank=True,
                choices=[('success', 'Success'), ('failure', 'Failure')],
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='epgrefreshstate',
            name='last_error',
            field=models.TextField(blank=True),
        ),
    ]
