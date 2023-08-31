# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cron',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('string', models.CharField(max_length=255, null=True, blank=True)),
                ('repeat_seconds', models.IntegerField(null=True, blank=True)),
                ('path', models.CharField(max_length=255)),
                ('parameters', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='CronResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField()),
                ('cron', models.ForeignKey(to='app_cron.Cron', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
    ]
