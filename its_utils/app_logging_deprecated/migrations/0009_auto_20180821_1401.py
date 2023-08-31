# Generated by Django 2.0.7 on 2018-08-21 11:01
# coding=utf-8
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_logging', '0008_auto_20180515_2319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logfromredis',
            name='level',
            field=models.IntegerField(choices=[(0, 'NOTSET'), (10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], verbose_name='Уровень'),
        ),
        migrations.AlterField(
            model_name='loggedscript',
            name='level_save_to_db',
            field=models.PositiveSmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=10, verbose_name='Уровень записи в БД'),
        ),
        migrations.AlterField(
            model_name='loggedscript',
            name='level_send_email',
            field=models.PositiveSmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=10, verbose_name='Уровень отсыла по E-mail'),
        ),
        migrations.AlterField(
            model_name='logtype',
            name='count_info',
            field=models.CharField(blank=True, default='', max_length=255, verbose_name='Количество записей'),
        ),
        migrations.AlterField(
            model_name='logtype',
            name='level_save_to_db',
            field=models.PositiveSmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=10, verbose_name='Уровень записи в БД'),
        ),
        migrations.AlterField(
            model_name='logtype',
            name='level_send_email',
            field=models.PositiveSmallIntegerField(choices=[(10, 'DEBUG'), (20, 'INFO'), (30, 'WARNING'), (40, 'ERROR'), (50, 'CRITICAL')], default=10, verbose_name='Уровень отсыла по E-mail'),
        ),
    ]
