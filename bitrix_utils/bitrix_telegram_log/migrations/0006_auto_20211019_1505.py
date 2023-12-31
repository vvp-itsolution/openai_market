# Generated by Django 3.2.5 on 2021-10-19 12:05

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_telegram_log', '0005_auto_20211018_2149'),
    ]

    operations = [
        migrations.AddField(
            model_name='portalchat',
            name='last_log_dt',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='portalchat',
            name='status_message_dt',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='portalchat',
            name='status_message_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
