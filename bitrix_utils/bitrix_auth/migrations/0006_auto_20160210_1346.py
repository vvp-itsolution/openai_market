# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-10 10:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0005_auto_20160210_1338'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bitrixportal',
            name='active',
        ),
        migrations.RemoveField(
            model_name='bitrixportal',
            name='scope',
        ),
        migrations.RemoveField(
            model_name='bitrixuser',
            name='status',
        ),
    ]
