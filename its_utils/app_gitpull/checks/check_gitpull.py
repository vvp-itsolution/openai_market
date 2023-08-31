# -*- coding: UTF-8 -*-


from django.conf import settings
from django.core.checks import Warning, register


@register()
def check_gitpull(app_configs, **kwargs):

    errors = []

    if 'its_utils.app_gitpull' not in getattr(settings, 'INSTALLED_APPS', []):
        errors.append(
            Warning(
                'No gitpull app installed',
                hint=None,
                obj='Warning',
                id='%s.W001' % 'check_gitpull',
            )
        )

    return errors
