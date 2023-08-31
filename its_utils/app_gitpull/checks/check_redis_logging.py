# -*- coding: UTF-8 -*-
from django.core.checks import register, Critical
from django.utils import timezone

from its_utils.app_logging.cron_functions import handle_redis_logs
from its_utils.app_logging.models import LogFromRedis

cron_freshness_seconds = 30


def run_test_redis_logging():
    import logging
    logging.getLogger('its.redis').debug('test debug')
    logging.getLogger('its.redis').info('test info')
    logging.getLogger('its.redis').warning('test warning')
    logging.getLogger('its.redis').error('test error')
    logging.getLogger('its.redis').critical('test critical')

    handle_redis_logs()


@register()
def check_redis_logging(app_configs, **kwargs):
    """
    Проверка работы сбора логов из redis.
    Запускаем тестовый сбор, проверяем, создавались ли записи за последние 30 секунд.
    """

    errors = []

    run_test_redis_logging()

    fresh_cron_time = timezone.now() - timezone.timedelta(seconds=cron_freshness_seconds)
    if not LogFromRedis.objects.filter(dt__gte=fresh_cron_time).exists():
        errors.append(
            Critical(
                'Redis logging is not working',
                hint=None,
                obj='Critical',
                id='%s.W001' % 'check_redis_logging',
            )
        )

    return errors
