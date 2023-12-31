# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-17 15:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.manager
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0010_bitrixuser_bitrix_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='BitrixDepartment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='bitrix_auth.BitrixDepartment')),
                ('portal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bitrix_auth.BitrixPortal')),
            ],
            managers=[
                #('_default_manager', django.db.models.manager.Manager()),
                ('objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='BitrixGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('portal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bitrix_auth.BitrixPortal')),
            ],
        ),
        migrations.CreateModel(
            name='BitrixUserGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bitrix_auth.BitrixGroup')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bitrix_auth.BitrixUser')),
            ],
        ),
    ]
