# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-12 15:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_cron', '0005_auto_20160204_1730'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cron',
            name='repeat_seconds',
            field=models.IntegerField(blank=True, help_text='\u0427\u0435\u0440\u0435\u0437 \u043a\u0430\u043a\u043e\u0435 \u043a\u043e\u043b\u0438\u0447\u0435\u0441\u0442\u0432\u043e \u0441\u0435\u043a\u0443\u043d\u0434 \u0437\u0430\u043f\u0443\u0441\u043a\u0430\u0442\u044c \u0437\u0430\u0434\u0430\u0447\u0443.\u0415\u0441\u043b\u0438 \u043f\u043e\u043b\u0435 \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0435\u043d\u043e, \u0442\u043e \u043a\u0440\u043e\u043d \u0441\u0442\u0440\u043e\u043a\u0430 \u0438\u0433\u043d\u043e\u0440\u0438\u0440\u0443\u0435\u0442\u0441\u044f', null=True),
        ),
    ]
