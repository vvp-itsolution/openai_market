# -*- coding: UTF-8 -*-
from django.conf import settings
from django.core.checks import register, Critical, Warning


@register()
def check_debug_mode(app_configs, **kwargs):
    """
    Проверка значения DEBUG в settings
    """

    errors = []
    if getattr(settings, 'DEBUG'):
        errors.append(
            Warning(
                'DEBUG is set to True in settings',
                hint=None,
                obj='Critical',
                id='%s.W001' % 'check_debug_mode',
            )
        )

    return errors
