# Generated by Django 2.2.1 on 2019-09-06 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_logger', '0006_auto_20190425_1850'),
    ]

    operations = [
        migrations.AddField(
            model_name='loggedapp',
            name='telegram_chat',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='logtype',
            name='telegram_chat',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
