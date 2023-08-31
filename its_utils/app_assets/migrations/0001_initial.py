# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AssetsFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u043d\u043e')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0435 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435')),
                ('file', models.FileField(upload_to=b'assets/files/%Y-%m-%d/', verbose_name='\u0424\u0430\u0439\u043b')),
            ],
            options={
                'verbose_name': '\u0444\u0430\u0439\u043b',
                'verbose_name_plural': '\u0444\u0430\u0439\u043b\u044b',
            },
        ),
        migrations.CreateModel(
            name='AssetsPicture',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name='\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u0421\u043e\u0437\u0434\u0430\u043d\u043e')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='\u041f\u043e\u0441\u043b\u0435\u0434\u043d\u0435\u0435 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435')),
                ('picture', models.ImageField(upload_to=b'assets/pictures/%Y-%m-%d/', verbose_name='\u041a\u0430\u0440\u0442\u0438\u043d\u043a\u0430')),
            ],
            options={
                'verbose_name': '\u043a\u0430\u0440\u0442\u0438\u043d\u043a\u0430',
                'verbose_name_plural': '\u043a\u0430\u0440\u0442\u0438\u043d\u043a\u0438',
            },
        ),
    ]
