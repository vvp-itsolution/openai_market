# Generated by Django 2.2.10 on 2020-05-12 16:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0059_auto_20200512_1800'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitrixnotification',
            name='error',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bitrixnotification',
            name='error_text',
            field=models.TextField(blank=True, null=True),
        ),
    ]
