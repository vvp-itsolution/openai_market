# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_email', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outgoingemail',
            name='bcc_soe',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='outgoingemail',
            name='cc_soe',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
