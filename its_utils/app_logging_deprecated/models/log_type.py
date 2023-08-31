# -*- coding: utf-8 -*-

import logging

from django.db import models
from django.utils import timezone


class LogType(models.Model):
    LEVEL_CHOICES = (
        (logging.DEBUG, 'DEBUG'),
        (logging.INFO, 'INFO'),
        (logging.WARNING, 'WARNING'),
        (logging.ERROR, 'ERROR'),
        (logging.CRITICAL, 'CRITICAL'),
    )

    name = models.CharField(u'Имя события', max_length=255)
    level_save_to_db = models.PositiveSmallIntegerField(u'Уровень записи в БД',
                                                        choices=LEVEL_CHOICES, default=logging.DEBUG)
    level_send_email = models.PositiveSmallIntegerField(u'Уровень отсыла по E-mail',
                                                        choices=LEVEL_CHOICES, default=logging.DEBUG)

    storage_days = models.IntegerField(u'Срок хранения записей (дни)', null=True, blank=True)
    count_info = models.CharField(u'Количество записей', max_length=255, default='', blank=True)

    class Meta:
        app_label = 'app_logging'

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name

    def count_logs(self):
        count = self.logfromredis_set.count()

        self.count_info = u'на {date} записей: {count}'.format(
            count=count,
            date=timezone.now().strftime('%d.%m.%Y %H:%M:%S')
        )
        self.save()

        return count

    def clean_logs(self):
        if self.storage_days:
            date = timezone.now().date() - timezone.timedelta(days=self.storage_days)
            self.logfromredis_set.filter(date__lt=date).delete()
