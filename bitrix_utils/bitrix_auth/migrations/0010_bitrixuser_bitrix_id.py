# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-16 12:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('bitrix_auth', '0009_auto_20160215_1144'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitrixuser',
            name='bitrix_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]