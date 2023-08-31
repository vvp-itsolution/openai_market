# -*- coding: utf-8 -*-

from django.db import models
from its_utils.functions import sys_call


class Script(models.Model):
    name = models.CharField(u'Название', max_length=100)
    source = models.TextField(u'Текст скрипта')

    def __unicode__(self):
        return self.name

    some_source = lambda self: self.source[:200]
    some_source.short_description = u'Часть кода'

    class Meta:
        verbose_name = u'Скрипт'
        verbose_name_plural = u'Скрипты'
        app_label = 'app_linuxshell'

    def execute(self):
        res, output = sys_call(self.source)
        text = "%s \n\r\n\r %s" % (res, output)
        return text