# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-20 10:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0012_auto_20160219_1537'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitrixdepartment',
            name='bitrix_id',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bitrixgroup',
            name='bitrix_id',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
