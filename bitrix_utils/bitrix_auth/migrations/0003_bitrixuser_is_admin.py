# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-10 16:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0002_bitrixuser_auth_token_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitrixuser',
            name='is_admin',
            field=models.BooleanField(default=False),
        ),
    ]
