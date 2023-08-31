# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OutgoingEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sender_soe', models.CharField(max_length=255)),
                ('from_soe', models.CharField(max_length=255)),
                ('to_soe', models.CharField(max_length=255)),
                ('cc_soe', models.CharField(max_length=255)),
                ('bcc_soe', models.CharField(max_length=255)),
                ('subject_soe', models.CharField(max_length=255)),
                ('text_content_soe', models.TextField()),
                ('html_content_soe', models.TextField()),
                ('is_sent_soe', models.BooleanField(default=False, db_index=True)),
            ],
        ),
    ]
