# -*- coding: utf-8 -*-
# Generated by Django 2.1.7 on 2019-04-22 08:22

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app_logger', '0004_auto_20190305_1915'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logrecord',
            name='date_time',
            field=models.DateTimeField(db_index=True,
                                       default=django.utils.timezone.now,
                                       verbose_name=u'Время'),
        ),
    ]
