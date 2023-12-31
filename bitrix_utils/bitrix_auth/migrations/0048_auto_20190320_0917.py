# -*- coding: utf-8 -*-
# Generated by Django 2.1.7 on 2019-03-20 06:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0048_rm_dupes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bitrixuser',
            name='is_admin',
            field=models.BooleanField(blank=True, default=False),
        ),
        migrations.AlterUniqueTogether(
            name='bitrixusertoken',
            unique_together={('application', 'user')},
        ),
    ]
