# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_cron', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cron',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='cron',
            name='concurrency',
            field=models.IntegerField(default=1, blank=True),
        ),
        migrations.AddField(
            model_name='cron',
            name='description',
            field=models.TextField(default=b'', blank=True),
        ),
    ]
