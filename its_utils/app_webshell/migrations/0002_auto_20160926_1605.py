# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-26 13:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_webshell', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='script',
            options={'verbose_name': '\u0421\u043a\u0440\u0438\u043f\u0442', 'verbose_name_plural': '\u0421\u043a\u0440\u0438\u043f\u0442\u044b'},
        ),
        migrations.AlterField(
            model_name='script',
            name='name',
            field=models.CharField(max_length=100, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435'),
        ),
        migrations.AlterField(
            model_name='script',
            name='source',
            field=models.TextField(verbose_name='\u0422\u0435\u043a\u0441\u0442 \u0441\u043a\u0440\u0438\u043f\u0442\u0430'),
        ),
    ]