# -*- coding: utf-8 -*-

import logging

from bitrix_utils.bitrix_auth.models import BitrixPortal, BitrixUser
from settings import ilogger


def check_users_tokens():
    """
    Проверить токены всех пользователей.
    Для каждого пользовтаеля:
        Обновить токен
        Проверить является ли пользователь админом
        Если еще надо проверить права доступа приложения
    """

    active_users_before = BitrixUser.objects.filter(user_is_active=True).count()
    active_count = 0

    for user in BitrixUser.objects.filter(user_is_active=True):
        # Обновление токена пользователя
        if user.refresh_auth_token():
            active_count += 1

    msg = u'Активные пользователи: %s -> %s' % (active_users_before, active_count)


    ilogger.info(u'check_users_tokens=>%s' % msg)

    return msg
