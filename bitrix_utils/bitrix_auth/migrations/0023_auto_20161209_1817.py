# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-09 15:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0022_bitrixusertoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitrixapp',
            name='redirect_url',
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='bitrixapp',
            name='scope',
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='bitrixusertoken',
            name='refresh_error',
            field=models.PositiveSmallIntegerField(choices=[(0, b'\xd0\x9d\xd0\xb5\xd1\x82 \xd0\xbe\xd1\x88\xd0\xb8\xd0\xb1\xd0\xba\xd0\xb8'), (1, b'\xd0\x9d\xd0\xb5 \xd1\x83\xd1\x81\xd1\x82\xd0\xb0\xd0\xbd\xd0\xbe\xd0\xb2\xd0\xbb\xd0\xb5\xd0\xbd \xd0\xbf\xd0\xbe\xd1\x80\xd1\x82\xd0\xb0\xd0\xbb (Wrong client)'), (2, b'\xd0\xa3\xd1\x81\xd1\x82\xd0\xb0\xd1\x80\xd0\xb5\xd0\xbb \xd0\xba\xd0\xbb\xd1\x8e\xd1\x87 \xd1\x81\xd0\xbe\xd0\xb2\xd1\x81\xd0\xb5\xd0\xbc (Expired token)'), (3, b'\xd0\x98\xd0\xbd\xd0\xb2\xd0\xb0\xd0\xbb\xd0\xb8\xd0\xb4 \xd0\xb3\xd1\x80\xd0\xb0\xd0\xbd\xd1\x82 (Invalid grant)'), (8, b'\xd0\xbe\xd1\x88\xd0\xb8\xd0\xb1\xd0\xba\xd0\xb0 >= 500 '), (9, b'\xd0\x9d\xd0\xb0\xd0\xb4\xd0\xbe \xd1\x80\xd0\xb0\xd0\xb7\xd0\xbe\xd0\xb1\xd1\x80\xd0\xb0\xd1\x82\xd1\x8c\xd1\x81\xd1\x8f (Unnown Error)')], default=0),
        ),
    ]
