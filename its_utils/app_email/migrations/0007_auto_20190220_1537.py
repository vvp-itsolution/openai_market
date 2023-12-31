# Generated by Django 2.1.2 on 2019-02-20 12:37

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app_email', '0006_auto_20180404_1234'),
    ]

    operations = [
        migrations.AddField(
            model_name='templatedoutgoingmail',
            name='date_create',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
        migrations.AddField(
            model_name='templatedoutgoingmail',
            name='date_sent',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='mailimage',
            name='image',
            field=models.ImageField(upload_to='app_email/images/'),
        ),
        migrations.AlterField(
            model_name='mailimage',
            name='name',
            field=models.CharField(default='', max_length=120),
        ),
        migrations.AlterField(
            model_name='mailtemplate',
            name='html',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='mailtemplate',
            name='subject',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='mailtemplate',
            name='text',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='templatedoutgoingmail',
            name='hash',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='templatedoutgoingmail',
            name='to_email',
            field=models.TextField(default=''),
        ),
    ]
