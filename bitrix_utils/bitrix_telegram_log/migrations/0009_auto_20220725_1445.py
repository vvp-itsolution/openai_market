# Generated by Django 2.2.14 on 2022-07-25 11:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_telegram_log', '0008_portalchat_muted_log_types'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portalchat',
            name='chat',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='bitrix_telegram_log.TelegramChat'),
        ),
    ]
