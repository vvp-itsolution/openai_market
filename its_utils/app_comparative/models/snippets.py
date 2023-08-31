# coding: utf-8

from django.db import models
from django.db.models import ForeignKey, TextField, CharField, IntegerField

from its_utils.app_comparative.models import Compared


class Snippet(models.Model):
    comparison = ForeignKey(Compared, blank=True, null=True)
    snippet = TextField()
    level = IntegerField(default=100, verbose_name=u'Уровень',
                         help_text=u'10 - мусор | 20 - script, css | 30 - ждет решения | 100 - статус не присвоен')

    def save(self, *args, **kwargs):
        self.snippet = '\n'.join(self.snippet.split('\r\n'))
        super(Snippet, self).save(*args, **kwargs)
