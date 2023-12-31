# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-03-05 16:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0036_auto_20180305_1812'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bitrixuser',
            name='auth_token',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.AlterField(
            model_name='bitrixuser',
            name='auth_token_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='bitrixuser',
            name='refresh_token',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
