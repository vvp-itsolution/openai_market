# Generated by Django 2.2.4 on 2019-08-16 08:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0054_auto_20190815_1743'),
    ]

    operations = [
        migrations.AddField(
            model_name='bitrixappinstallation',
            name='application_token',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
