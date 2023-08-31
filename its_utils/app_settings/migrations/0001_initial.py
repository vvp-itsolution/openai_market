# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='KeyValue',
            fields=[
                ('key', models.SlugField(serialize=False, verbose_name='\u043a\u043b\u044e\u0447', primary_key=True)),
                ('value', models.TextField(verbose_name='\u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435')),
                ('comment', models.TextField(verbose_name='\u043a\u043e\u043c\u043c\u0435\u043d\u0442\u0430\u0440\u0438\u0439', blank=True)),
            ],
        ),
    ]
