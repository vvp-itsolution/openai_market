# -*- coding: utf-8 -*-

from django.db import models
from django.utils import timezone

from its_utils.app_admin.action_admin import ActionAdmin
from its_utils.app_logger.utils import log_levels
from settings import ilogger


class LogType(models.Model):
    """
    Тип записи
    """

    name = models.CharField(max_length=255, unique=True)

    level_save_to_db = models.PositiveSmallIntegerField(u'Уровень записи в БД',
                                                        choices=log_levels.LOG_LEVEL_CHOICES,
                                                        default=log_levels.DEBUG)

    level_send_email = models.PositiveSmallIntegerField(u'Уровень отсыла по E-mail',
                                                        choices=log_levels.LOG_LEVEL_CHOICES,
                                                        default=log_levels.DEBUG)

    level_send_telegram = models.PositiveSmallIntegerField(u'Уровень отсыла в Telegram',
                                                           choices=log_levels.LOG_LEVEL_CHOICES,
                                                           default=log_levels.DEBUG)

    storage_days = models.IntegerField(u'Срок хранения записей (дни)', null=True, blank=True)
    count_info = models.CharField(u'Количество записей', max_length=255, default='', blank=True)
    telegram_chat = models.CharField(blank=True, max_length=255)
    postpone = models.DateField(u'Отложить логгирование до', blank=True, null=True)

    class Meta:
        app_label = 'app_logger'

    class Admin(ActionAdmin):
        list_display = (
        'name', 'level_save_to_db', 'level_send_email', 'level_send_telegram', 'storage_days', 'count_info',
        'telegram_chat')
        list_editable = ['level_save_to_db', 'level_send_email', 'level_send_telegram', 'telegram_chat']
        readonly_fields = ('id',)
        actions = ['count_logs']

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        ilogger.types_dict.pop(self.name, None)
        super(LogType, self).save(*args, **kwargs)

    __str__ = __unicode__

    def clean_logs(self):
        count = 0
        if self.storage_days:
            date = timezone.now().date() - timezone.timedelta(days=self.storage_days)
            while True:
                from its_utils.app_logger.models import LogRecord
                chunk = LogRecord.objects.filter(type_id=self.id, date__lt=date).only("id")[:1000]
                if chunk.count():
                    count += chunk.count()
                    self.logrecord_set.filter(id__in=chunk).delete()
                else:
                    break

        return count

    @classmethod
    def count_logs(cls):
        '''
            :admin_action_description: Посчитать количество записей по типу
        '''
        for log_type in LogType.objects.all():
            log_type.count_info = log_type.logrecord_set.all().count()
            log_type.save()
        return 'ok'