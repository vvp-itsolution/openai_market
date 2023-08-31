# coding: utf-8
# Generated by Django 2.0.2 on 2018-03-12 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0037_auto_20180305_1929'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bitrixaccessobject',
            name='type',
            field=models.PositiveSmallIntegerField(choices=[(0, 'user'), (1, 'group'), (2, 'department'), (3, 'system_group')]),
        ),
        migrations.AlterField(
            model_name='bitrixportal',
            name='scope',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='bitrixuser',
            name='facebook',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='bitrixuser',
            name='first_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='bitrixuser',
            name='last_name',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='bitrixuser',
            name='linkedin',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='bitrixuser',
            name='personal_mobile',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='bitrixuser',
            name='refresh_error',
            field=models.PositiveSmallIntegerField(choices=[(0, u'Нет ошибки'), (1, u'Не установлен портал (Wrong client)'), (2, u'Устарел ключ совсем (Expired token)'), (3, u'Инвалид грант (Invalid grant)'), (9, u'Надо разобраться (Unnown Error)')], default=0),
        ),
        migrations.AlterField(
            model_name='bitrixuser',
            name='skype',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='bitrixuser',
            name='twitter',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='bitrixuser',
            name='work_phone',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='bitrixusertoken',
            name='refresh_error',
            field=models.PositiveSmallIntegerField(choices=[(0, u'Нет ошибки'), (1, u'Не установлен портал (Wrong client)'), (2, u'Устарел ключ совсем (Expired token)'), (3, u'Инвалид грант (Invalid grant)'), (4, u'Не установлен портал (NOT_INSTALLED)'), (5, u'Не оплачено (PAYMENT_REQUIRED)'), (6, u'Домен отключен или не существует'), (8, u'ошибка >= 500 '), (9, u'Надо разобраться (Unknown Error)'), (10, u'PORTAL_DELETED'), (11, u'ERROR_CORE'), (12, u'ERROR_OAUTH'), (13, u'ERROR_403_or_404'), (14, u'NO_AUTH_FOUND'), (15, u'AUTHORIZATION_ERROR')], default=0),
        ),
    ]
