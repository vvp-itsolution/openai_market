# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-05 16:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_cron', '0009_cronlog_process'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cronlog',
            name='ended',
        ),
        migrations.AddField(
            model_name='cronlog',
            name='stopped',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='cronlog',
            name='started',
            field=models.DateField(null=True),
        ),
    ]
