# -*- coding: UTF-8 -*-
from django.core.checks import register, Critical

from its_utils.app_cron.models import Cron

logging_cron_path = 'its_utils.app_logging.cron_functions.handle_redis_logs'
logging_cron_name = 'handle_redis_logs'
logging_cron_string = '* * * * *'


@register()
def check_app_logging_cron(app_configs, **kwargs):
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
            Critical(
                'its_utils.app_logging.handle_redis_logs cron is not set correctly',
                hint=None,
                obj='Critical',
                id='%s.W001' % 'check_app_logging_cron',
            )
        )

    return errors
