# Generated by Django 2.2.1 on 2023-05-08 20:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_disk', '0002_bitrixfile_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitrixfile',
            name='last_check_access',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
