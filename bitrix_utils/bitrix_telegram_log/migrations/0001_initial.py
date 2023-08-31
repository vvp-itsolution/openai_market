# Generated by Django 3.2.5 on 2021-10-08 18:30

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import its_utils.app_telegram_bot.models.abstract_message
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bitrix_auth', '0062_auto_20210301_2250'),
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramChat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.CharField(max_length=100)),
                ('telegram_type', models.CharField(blank=True, choices=[('private', 'private'), ('group', 'group'), ('supergroup', 'supergroup')], default='', max_length=25, null=True)),
                ('secret', models.CharField(blank=True, default='', max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='TelegramLogBot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(default='', max_length=100)),
                ('auth_token', models.CharField(default='', max_length=100)),
                ('last_update_id', models.IntegerField(blank=True, default=0)),
                ('is_active', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='TelegramUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.CharField(max_length=100)),
                ('username', models.CharField(blank=True, default='', max_length=100, null=True)),
                ('first_name', models.CharField(blank=True, default='', max_length=127, null=True)),
                ('last_name', models.CharField(blank=True, default='', max_length=127, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TelegramMessage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.IntegerField()),
                ('text', models.TextField(default='', null=True)),
                ('date', models.DateTimeField(default=django.utils.timezone.now)),
                ('voice', models.FileField(blank=True, null=True, upload_to=its_utils.app_telegram_bot.models.abstract_message.voice_upload_path)),
                ('caption', models.TextField(default='', null=True)),
                ('effective_attachment', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bitrix_telegram_log.telegramuser')),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='bitrix_telegram_log.telegramchat')),
            ],
        ),
        migrations.AddField(
            model_name='telegramchat',
            name='bot',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='bitrix_telegram_log.telegramlogbot'),
        ),
        migrations.CreateModel(
            name='PortalChat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('secret', models.UUIDField(default=uuid.uuid4)),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='bitrix_auth.bitrixapp')),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='bitrix_telegram_log.telegramchat')),
                ('portal', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='bitrix_auth.bitrixportal')),
            ],
        ),
        migrations.CreateModel(
            name='LogBotApp',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='bitrix_auth.bitrixapp')),
                ('bot', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='bitrix_telegram_log.telegramlogbot')),
            ],
        ),
    ]
