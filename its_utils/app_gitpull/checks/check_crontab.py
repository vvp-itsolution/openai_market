# -*- coding: UTF-8 -*-
from django.core.checks import register, Critical, Warning
from django.utils import timezone

from its_utils.app_cron.models import CronLog

cron_sec_rate = 120


@register()
def check_crontab(app_configs, **kwargs):
    errors = []
    last_cron = CronLog.objects.order_by('started').last()
    if not last_cron or (timezone.now() - last_cron.started).seconds > cron_sec_rate:
        errors.append(
            Warning(
                'crontab is not set on server',
                hint=None,
                obj='Critical',
                id='%s.W001' % 'check_crontab',
            )
        )

    return errors
