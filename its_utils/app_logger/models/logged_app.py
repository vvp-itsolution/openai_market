# coding: utf-8
from django.db import models

from its_utils.app_logger.utils import log_levels
from django.contrib import admin

class LoggedApp(models.Model):
    """
    Логируемое приложение
    """

    name = models.CharField(max_length=255)

    level_save_to_db = models.PositiveSmallIntegerField(u'Уровень записи в БД',
                                                        choices=log_levels.LOG_LEVEL_CHOICES,
                                                        default=log_levels.DEBUG)

    level_send_email = models.PositiveSmallIntegerField(u'Уровень отсыла по E-mail',
                                                        choices=log_levels.LOG_LEVEL_CHOICES,
                                                        default=log_levels.CRITICAL)

    level_send_telegram = models.PositiveSmallIntegerField(u'Уровень отсыла в Telegram',
                                                           choices=log_levels.LOG_LEVEL_CHOICES,
                                                           default=log_levels.DEBUG)
    telegram_chat = models.CharField(blank=True, max_length=255)

    class Meta:
        app_label = 'app_logger'

    class Admin(admin.ModelAdmin):
        list_display = ['name', 'level_save_to_db', 'level_send_email', 'level_send_telegram', 'telegram_chat']
        list_editable = ['level_save_to_db', 'level_send_email', 'level_send_telegram', 'telegram_chat']
        #readonly_fields = ('id',)

    def __unicode__(self):
        return self.name

    __str__ = __unicode__
