# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-09-13 14:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_email', '0003_emailsettings'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailsettings',
            name='port',
            field=models.IntegerField(blank=True, default=587, null=True),
        ),
    ]
