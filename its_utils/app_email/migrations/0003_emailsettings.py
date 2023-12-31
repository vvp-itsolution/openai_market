# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-09-13 09:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_email', '0002_auto_20160614_1656'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host', models.CharField(default='', max_length=255)),
                ('port', models.SmallIntegerField(blank=True, null=True)),
                ('username', models.CharField(blank=True, default='', max_length=255)),
                ('password', models.CharField(blank=True, default='', max_length=255)),
                ('use_tls', models.BooleanField(default=False)),
                ('use_ssl', models.BooleanField(default=False)),
                ('sender_email', models.CharField(default='', max_length=255)),
            ],
        ),
    ]
