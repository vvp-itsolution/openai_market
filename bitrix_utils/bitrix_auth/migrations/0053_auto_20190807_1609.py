# Generated by Django 2.2.1 on 2019-08-07 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bitrix_auth', '0052_merge_20190807_1609'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bitrixdepartment',
            name='level',
            field=models.PositiveIntegerField(db_index=True, editable=False),
        ),
        migrations.AlterField(
            model_name='bitrixdepartment',
            name='lft',
            field=models.PositiveIntegerField(db_index=True, editable=False),
        ),
        migrations.AlterField(
            model_name='bitrixdepartment',
            name='rght',
            field=models.PositiveIntegerField(db_index=True, editable=False),
        ),
    ]
