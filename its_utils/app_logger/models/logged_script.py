# -*- coding: utf-8 -*-

from django.db import models
from its_utils.app_logger.utils import log_levels
from django.contrib import admin


class LoggedScript(models.Model):
    """
    Логируемый скрипт. Здесь хранятся настройки per-script, при каких уровнях лог из редиса будет попадать дальше
    (в БД, на почту).
    """

    pathname = models.CharField(u'Путь к скрипту', max_length=200, unique=True)

    level_save_to_db = models.PositiveSmallIntegerField(u'Уровень записи в БД',
                                                        choices=log_levels.LOG_LEVEL_CHOICES, default=log_levels.DEBUG)

    level_send_email = models.PositiveSmallIntegerField(u'Уровень отсыла по E-mail',
                                                        choices=log_levels.LOG_LEVEL_CHOICES, default=log_levels.DEBUG)

    level_send_telegram = models.PositiveSmallIntegerField(u'Уровень отсыла в Telegram',
                                                           choices=log_levels.LOG_LEVEL_CHOICES,
                                                           default=log_levels.DEBUG)

    class Meta:
        app_label = 'app_logger'

    class Admin(admin.ModelAdmin):
        list_display = ('pathname', 'level_save_to_db', 'level_send_email')
        readonly_fields = ('id',)

    def __unicode__(self):
        return self.pathname

    __str__ = __unicode__
