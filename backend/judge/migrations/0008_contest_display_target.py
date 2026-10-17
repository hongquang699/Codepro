from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('judge', '0007_submission_system_verdicts'),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='display_target',
            field=models.CharField(
                choices=[('both', 'Web và client'), ('web', 'Chỉ web'), ('client', 'Chỉ client')],
                default='both',
                max_length=6,
            ),
        ),
    ]
