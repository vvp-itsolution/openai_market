# -*- coding: UTF-8 -*-
import socket

from django.conf import settings
from django.core.checks import register, Critical, Warning
from django.core.mail.message import EmailMessage


@register()
def check_mail_settings(app_configs, **kwargs):
    errors = []
    attributes = ('ADMINS', 'EMAIL_HOST', 'SERVER_EMAIL')
    message = ''

    passed = all([getattr(settings, attr) for attr in attributes])

    if passed:
        try:
            EmailMessage().get_connection().open()
        except socket.error:
            passed = False
            message = 'Failed to connect to email server'

    else:
        message = 'ADMINS and EMAIL settings was not set correctly'

    if not passed:
        errors.append(
            Warning(
                message,
                hint=None,
                obj='Critical',
                id='%s.W001' % 'check_mail_settings',
            )
        )

    return errors
