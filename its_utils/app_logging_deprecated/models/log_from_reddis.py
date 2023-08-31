# -*- coding: utf-8 -*-

import logging

from django.db import models
from django.utils import timezone

from its_utils.app_admin.get_admin_url import get_admin_url
from its_utils.app_logging.models import LogType
from its_utils.functions import datetime_to_string


class LogFromRedis(models.Model):


    LEVEL_CHOICES = [
        (0, 'NOTSET'),
        (10, 'DEBUG'),
        (20, 'INFO'),
        (30, 'WARNING'),
        (40, 'ERROR'),
        (50, 'CRITICAL'),
    ]

    name = models.CharField(u'Логгер', max_length=50)
    level = models.IntegerField(u'Уровень', choices=LEVEL_CHOICES)
    type = models.ForeignKey(LogType, verbose_name=u'Тип', null=True, blank=True, on_delete=models.PROTECT)
    pathname = models.CharField(u'Путь к скрипту', max_length=200)
    lineno = models.IntegerField(u'Номер строки', null=True)
    msg = models.TextField(u'Сообщение', blank=True)
    exception = models.TextField(u'Исключение', blank=True)
    dt = models.DateTimeField(u'Дата', default=timezone.now)
    date = models.DateField(u"Дата", default=timezone.now, db_index=True)

    some_msg = lambda self: self.msg[:200]
    some_msg.short_description = u'Сообщение'

    from its_utils.django_postgres_fuzzycount.fuzzycount import FuzzyCountManager
    objects = FuzzyCountManager()

    @property
    def pretty_message(self):
        # return u'[%s][%s](%s)(%s)(%s)\n' \
        #        u'%s\n%s' % (self.name, self.get_level_display(), self.pathname, self.lineno, datetime_to_string(self.dt),
        #                     self.msg, self.exception)
        return u'[%s][%s](%s)(%s)(%s)\n' \
               u'%s %s' % (
               self.name, self.get_level_display(), self.pathname, self.lineno, datetime_to_string(self.dt),
               self.msg, get_admin_url(self))

    class Meta:
        app_label = 'app_logging'
