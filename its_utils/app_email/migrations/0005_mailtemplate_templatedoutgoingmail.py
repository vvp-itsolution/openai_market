# -*- coding: utf-8 -*-
# Generated by Django 1.11.10 on 2018-04-03 12:34
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_email', '0004_auto_20170913_1709'),
    ]

    operations = [
        migrations.CreateModel(
            name='MailTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(default=b'', max_length=255)),
                ('html', models.TextField(default=b'')),
                ('text', models.TextField(default=b'')),
            ],
        ),
        migrations.CreateModel(
            name='TemplatedOutgoingMail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('to_email', models.TextField(default=b'')),
                ('hash', models.CharField(blank=True, default=b'', max_length=100)),
                ('read', models.DateTimeField(blank=True, null=True)),
                ('from_email', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app_email.EmailSettings')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app_email.MailTemplate')),
            ],
        ),
    ]
