# Generated by Django 2.2.14 on 2020-08-10 11:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_release', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='release',
            name='application',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='app_release.Application'),
        ),
        migrations.AlterField(
            model_name='release',
            name='file',
            field=models.FileField(upload_to='release'),
        ),
        migrations.AlterField(
            model_name='release',
            name='state',
            field=models.SmallIntegerField(choices=[(0, 'Disabled'), (1, 'Test'), (2, 'Production')], default=1, verbose_name='Состояние'),
        ),
    ]
