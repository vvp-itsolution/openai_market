# coding: utf-8
# Generated by Django 2.0.5 on 2018-07-10 11:49

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='LoggedApp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('level_save_to_db', models.PositiveSmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=10, verbose_name=u'Уровень записи в БД')),
                ('level_send_email', models.PositiveSmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=10, verbose_name=u'Уровень отсыла по E-mail')),
            ],
        ),
        migrations.CreateModel(
            name='LoggedScript',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pathname', models.CharField(max_length=200, verbose_name=u'Путь к скрипту')),
                ('level_save_to_db', models.PositiveSmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=10, verbose_name=u'Уровень записи в БД')),
                ('level_send_email', models.PositiveSmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=10, verbose_name=u'Уровень отсыла по E-mail')),
            ],
        ),
        migrations.CreateModel(
            name='LogRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.SmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=20, verbose_name=u'Уровень')),
                ('date_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name=u'Время')),
                ('message', models.TextField(default='', verbose_name=u'Сообщение')),
                ('exception_info', models.TextField(default='', verbose_name=u'Исключение')),
                ('lineno', models.IntegerField(null=True, verbose_name=u'Номер строки')),
                ('params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name=u'Параметры')),
                ('app', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app_logger.LoggedApp', verbose_name=u'Приложение')),
                ('script', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_logger.LoggedScript', verbose_name=u'Скрипт')),
            ],
        ),
        migrations.CreateModel(
            name='LogType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('level_save_to_db', models.PositiveSmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=10, verbose_name=u'Уровень записи в БД')),
                ('level_send_email', models.PositiveSmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=10, verbose_name=u'Уровень отсыла по E-mail')),
                ('storage_days', models.IntegerField(blank=True, null=True, verbose_name=u'Срок хранения записей (дни)')),
                ('count_info', models.CharField(blank=True, default='', max_length=255, verbose_name=u'Количество записей')),
            ],
        ),
        migrations.AddField(
            model_name='logrecord',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_logger.LogType', verbose_name=u'Тип'),
        ),
    ]
