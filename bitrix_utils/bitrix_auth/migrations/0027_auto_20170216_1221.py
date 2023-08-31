# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-02-16 09:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0026_auto_20170122_2017'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitrixuser',
            name='facebook',
            field=models.CharField(blank=True, default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='bitrixuser',
            name='linkedin',
            field=models.CharField(blank=True, default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='bitrixuser',
            name='personal_mobile',
            field=models.CharField(blank=True, default=b'', max_length=100),
        ),
        migrations.AddField(
            model_name='bitrixuser',
            name='skype',
            field=models.CharField(blank=True, default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='bitrixuser',
            name='twitter',
            field=models.CharField(blank=True, default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='bitrixuser',
            name='work_phone',
            field=models.CharField(blank=True, default=b'', max_length=100),
        ),
    ]
