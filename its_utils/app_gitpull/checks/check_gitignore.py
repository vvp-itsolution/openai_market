# -*- coding: UTF-8 -*-

import os

from django.conf import settings
from django.core.checks import Warning, register
from its_utils.app_gitpull import gitpull_settings


APPS_TO_CHECK = gitpull_settings.APPS_TO_CHECK


@register()
def check_gitignore(app_configs, **kwargs):

    errors = []

    try:
        open(os.path.join(settings.BASE_DIR, '.gitignore'))
    except IOError as e:
        errors.append(
            Warning(
                'No gitignore file found',
                hint=None,
                obj='Warning',
                id='%s.W001' % 'check_gitignore',
            )
        )

    return errors
