# Generated by Django 3.2.2 on 2023-05-11 09:36

import bitrix_utils.bitrix_disk.models.bitrix_file
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_disk', '0003_bitrixfile_last_check_access'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bitrixfile',
            name='file',
            field=models.FileField(blank=True, max_length=255, null=True, upload_to=bitrix_utils.bitrix_disk.models.bitrix_file.file_path),
        ),
    ]
