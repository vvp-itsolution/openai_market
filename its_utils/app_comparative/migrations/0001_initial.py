# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-09-15 16:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Compared',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url1', models.CharField(max_length=255, verbose_name='Url 1')),
                ('url2', models.CharField(max_length=255, verbose_name='Url 2')),
            ],
        ),
    ]
