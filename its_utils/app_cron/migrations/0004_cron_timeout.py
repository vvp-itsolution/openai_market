# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_cron', '0003_auto_20151228_1026'),
    ]

    operations = [
        migrations.AddField(
            model_name='cron',
            name='timeout',
            field=models.FloatField(null=True, blank=True),
        ),
    ]
