# Generated by Django 3.1.6 on 2021-04-06 13:48

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('app_logger', '0013_auto_20201129_1326'),
        ('bitrix_auth', '0062_auto_20210301_2250'),
    ]

    operations = [
        migrations.CreateModel(
            name='PortalLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.SmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=20, verbose_name='Уровень')),
                ('date_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Время')),
                ('date', models.DateField(default=django.utils.timezone.now, null=True, verbose_name='Дата')),
                ('message', models.TextField(default='', verbose_name='Сообщение')),
                ('exception_info', models.TextField(default='', verbose_name='Исключение')),
                ('lineno', models.IntegerField(null=True, verbose_name='Номер строки')),
                ('tag', models.CharField(blank=True, db_index=True, default='', max_length=50, null=True, verbose_name='Метка для фильтрации')),
                ('params', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True, verbose_name='Параметры')),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_logger.loggedapp', verbose_name='Приложение')),
                ('portal', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bitrix_auth.bitrixportal')),
                ('script', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_logger.loggedscript', verbose_name='Скрипт')),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_logger.logtype', verbose_name='Тип')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
