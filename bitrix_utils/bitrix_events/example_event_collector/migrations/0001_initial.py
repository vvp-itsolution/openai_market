# Generated by Django 2.2.4 on 2019-08-26 11:14

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bitrix_auth', '0056_bitrix_app_installation_application_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='PortalEventSetting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lock_dt_for_collect_events', models.DateTimeField(blank=True, null=True, verbose_name='Время взятия в обработку')),
                ('force_collect_events', models.BooleanField(db_index=True, default=False, verbose_name='Запустить принудительно сбор событий')),
                ('last_collect_events', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Время последнего получения событий')),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(default=dict, verbose_name='Дополнительные данные')),
                ('install_date', models.DateTimeField(default=django.utils.timezone.now, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('portal', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='bitrix_auth.BitrixPortal')),
            ],
            options={
                'verbose_name': 'Настройки портала',
                'verbose_name_plural': 'Настройки порталов',
            },
        ),
        migrations.CreateModel(
            name='CollectorBitrixEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_name', models.CharField(default='', max_length=127)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(default=dict)),
                ('datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('portal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bitrix_auth.BitrixPortal')),
            ],
        ),
    ]
