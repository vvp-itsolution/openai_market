# -*- coding: utf-8 -*-

import logging

from django.db import models


class LoggedScript(models.Model):
    """
    Логируемый скрипт. Здесь хранятся настройки per-script, при каких уровнях лог из редиса будет попадать дальше
    (в БД, на почту).
    """
    LEVEL_CHOICES = (
        (logging.DEBUG, 'DEBUG'),
        (logging.INFO, 'INFO'),
        (logging.WARNING, 'WARNING'),
        (logging.ERROR, 'ERROR'),
        (logging.CRITICAL, 'CRITICAL'),
    )

    pathname = models.CharField(u'Путь к скрипту', max_length=200)
    level_save_to_db = models.PositiveSmallIntegerField(u'Уровень записи в БД',
                                                        choices=LEVEL_CHOICES, default=logging.DEBUG)
    level_send_email = models.PositiveSmallIntegerField(u'Уровень отсыла по E-mail',
                                                        choices=LEVEL_CHOICES, default=logging.DEBUG)

    class Meta:
        app_label = 'app_logging'
