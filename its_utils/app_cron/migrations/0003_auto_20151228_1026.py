# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_cron', '0002_auto_20151228_1015'),
    ]

    operations = [
        migrations.AddField(
            model_name='cronresult',
            name='end',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='cronresult',
            name='start',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='cronresult',
            name='text',
            field=models.TextField(null=True),
        ),
    ]
