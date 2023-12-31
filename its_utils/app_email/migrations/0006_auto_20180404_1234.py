# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-04-04 09:34
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_email', '0005_mailtemplate_templatedoutgoingmail'),
    ]

    operations = [
        migrations.CreateModel(
            name='MailImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default=b'', max_length=120)),
                ('image', models.ImageField(upload_to=b'app_email/images/')),
            ],
        ),
        migrations.AddField(
            model_name='templatedoutgoingmail',
            name='params',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='mailtemplate',
            name='html',
            field=models.TextField(blank=True, default=b''),
        ),
        migrations.AlterField(
            model_name='mailtemplate',
            name='text',
            field=models.TextField(blank=True, default=b''),
        ),
    ]
