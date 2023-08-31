# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Release',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(default=django.utils.timezone.now)),
                ('comment', models.TextField(null=True, verbose_name='\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435', blank=True)),
                ('state', models.SmallIntegerField(default=1, verbose_name='\u0421\u043e\u0441\u0442\u043e\u044f\u043d\u0438\u0435', choices=[(0, b'Disabled'), (1, b'Test'), (2, b'Production')])),
                ('file', models.FileField(upload_to=b'release')),
                ('application', models.ForeignKey(to='app_release.Application', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
    ]
