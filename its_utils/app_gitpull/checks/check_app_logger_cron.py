# -*- coding: UTF-8 -*-
from django.core.checks import register, Critical, Warning

from its_utils.app_cron.models import Cron

logging_cron_path = 'its_utils.app_logger.functions.cron.process_log_records'
logging_cron_name = 'App logger: process log records'
logging_cron_string = '* * * * *'


@register()
def check_app_logger_cron(app_configs, **kwargs):
    """
    Проверка записи сбора логов в cron-таблице.
    Запись должна существовать, быть активной и запускаться не реже, чем раз в минуту
    """

    errors = []

    # Если записи нет, создаём, но не активируем
    cron, _ = Cron.objects.get_or_create(path=logging_cron_path, defaults=dict(
        name=logging_cron_name, string=logging_cron_string, active=False
    ))

    if (cron.string != logging_cron_string and (
            not cron.repeat_seconds or cron.repeat_seconds > 60
    )) or not cron.active:
        errors.append(
            Warning(
                'its_utils.app_logger.functions.cron.process_log_records cron is not set correctly',
                hint=None,
                obj='Critical',
                id='%s.W001' % 'check_app_logger_cron',
            )
        )

    return errors
