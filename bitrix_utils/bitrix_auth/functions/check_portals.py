# -*- coding: utf-8 -*-

import logging

from bitrix_utils.bitrix_auth.models import BitrixPortal, BitrixUser
from bitrix_utils.bitrix_auth.functions.check_users_tokens import check_users_tokens
from settings import ilogger


def check_portals():
    """
    Проверить статус порталов.
    """

    check_users_tokens()

    portals = BitrixPortal.objects.all()
    active_portals_before = portals.filter(active=True).count()

    for portal in portals:
        portal.active = False
        for user in BitrixUser.objects.filter(portal=portal):
            if user.user_is_active:
                portal.active = True
                break
        portal.save()

    active_portals_after = BitrixPortal.objects.filter(active=True).count()
    msg = u'check_portals=>Активные порталы %s %s' % (active_portals_before, active_portals_after)
    ilogger.info(msg)
    return msg
