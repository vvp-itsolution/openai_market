# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-05-15 20:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_logging', '0007_auto_20180317_0111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logtype',
            name='name',
            field=models.CharField(max_length=255, verbose_name='\u0418\u043c\u044f \u0441\u043e\u0431\u044b\u0442\u0438\u044f'),
        ),
    ]
