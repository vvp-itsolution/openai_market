# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-09-18 17:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0045_auto_20180823_1413'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitrixusertoken',
            name='app_sid',
            field=models.CharField(blank=True, max_length=70),
        ),
    ]
