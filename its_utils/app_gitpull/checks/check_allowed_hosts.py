# -*- coding: UTF-8 -*-

from django.conf import settings
from django.core.checks import Warning, register


@register()
def check_allowed_hosts(app_configs, **kwargs):

    errors = []

    if not getattr(settings, 'ALLOWED_HOSTS'):
        errors.append(
            Warning(
                'ALLOWED_HOSTS was not set correctly',
                hint=None,
                obj='Warning',
                id='%s.W001' % 'check_allowed_hosts',
            )
        )

    return errors
