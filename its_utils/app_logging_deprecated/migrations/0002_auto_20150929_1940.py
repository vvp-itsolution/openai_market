# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app_logging', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoggedScript',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pathname', models.CharField(max_length=200, verbose_name='\u041f\u0443\u0442\u044c \u043a \u0441\u043a\u0440\u0438\u043f\u0442\u0443')),
                ('level_save_to_db', models.PositiveSmallIntegerField(default=10, verbose_name='\u0423\u0440\u043e\u0432\u0435\u043d\u044c \u0437\u0430\u043f\u0438\u0441\u0438 \u0432 \u0411\u0414', choices=[(10, b'DEBUG'), (20, b'INFO'), (30, b'WARNING'), (40, b'ERROR'), (50, b'CRITICAL')])),
                ('level_send_email', models.PositiveSmallIntegerField(default=10, verbose_name='\u0423\u0440\u043e\u0432\u0435\u043d\u044c \u043e\u0442\u0441\u044b\u043b\u0430 \u043f\u043e E-mail', choices=[(10, b'DEBUG'), (20, b'INFO'), (30, b'WARNING'), (40, b'ERROR'), (50, b'CRITICAL')])),
            ],
        ),
        migrations.CreateModel(
            name='LogType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, verbose_name='\u0418\u043c\u044f \u0441\u043e\u0431\u044b\u0442\u0438\u044f')),
                ('mute', models.BooleanField(default=False, verbose_name='\u0417\u0430\u043c\u0430\u043b\u0447\u0438\u0432\u0430\u0442\u044c')),
            ],
        ),
        migrations.AlterField(
            model_name='logfromredis',
            name='dt',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='\u0414\u0430\u0442\u0430'),
        ),
        migrations.AlterField(
            model_name='logfromredis',
            name='exception',
            field=models.TextField(verbose_name='\u0418\u0441\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435', blank=True),
        ),
        migrations.AlterField(
            model_name='logfromredis',
            name='level',
            field=models.IntegerField(verbose_name='\u0423\u0440\u043e\u0432\u0435\u043d\u044c'),
        ),
        migrations.AlterField(
            model_name='logfromredis',
            name='lineno',
            field=models.IntegerField(null=True, verbose_name='\u041d\u043e\u043c\u0435\u0440 \u0441\u0442\u0440\u043e\u043a\u0438'),
        ),
        migrations.AlterField(
            model_name='logfromredis',
            name='msg',
            field=models.TextField(verbose_name='\u0421\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435', blank=True),
        ),
        migrations.AlterField(
            model_name='logfromredis',
            name='name',
            field=models.CharField(max_length=50, verbose_name='\u041b\u043e\u0433\u0433\u0435\u0440'),
        ),
        migrations.AlterField(
            model_name='logfromredis',
            name='pathname',
            field=models.CharField(max_length=200, verbose_name='\u041f\u0443\u0442\u044c \u043a \u0441\u043a\u0440\u0438\u043f\u0442\u0443'),
        ),
    ]
