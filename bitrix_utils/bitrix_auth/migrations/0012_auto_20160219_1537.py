# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-19 12:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0011_bitrixdepartment_bitrixgroup_bitrixusergroup'),
    ]

    operations = [
        migrations.CreateModel(
            name='BitrixAccessObject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.PositiveSmallIntegerField(choices=[(0, b'user'), (1, b'group'), (2, b'department'), (3, b'system_group')])),
                ('type_id', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='BitrixAccessObjectSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AddField(
            model_name='bitrixaccessobject',
            name='set',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bitrix_auth.BitrixAccessObjectSet'),
        ),
    ]
