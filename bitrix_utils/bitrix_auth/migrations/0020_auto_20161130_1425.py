# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-30 11:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0019_auto_20160926_2036'),
    ]

    operations = [
        migrations.CreateModel(
            name='BitrixApp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bitrix_client_id', models.CharField(blank=True, max_length=100)),
                ('bitrix_client_secret', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='bitrixuser',
            name='application',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bitrix_auth.BitrixApp'),
        ),
    ]
