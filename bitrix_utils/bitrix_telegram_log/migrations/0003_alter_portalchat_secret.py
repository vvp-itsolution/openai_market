# Generated by Django 3.2.5 on 2021-10-08 20:35

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_telegram_log', '0002_auto_20211008_2138'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portalchat',
            name='secret',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
