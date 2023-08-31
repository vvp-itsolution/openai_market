# -*- coding: utf-8 -*-

from bitrix_utils.bitrix_auth.models import BitrixGroup, BitrixUserGroup


def update_user_groups(user, user_groups):

    """
    Для данного пользователя обновить список социальных групп, в которых он состоит
    user - объект BitrixUser
    user_groups - список групп в том виде, как его возвращает метод битрикса sonet_group.user.groups
    Возвращает список созданных объектов.
    """

    result = []
    for g in user_groups:
        group, _ = BitrixGroup.objects.get_or_create(portal_id=user.portal_id, bitrix_id=g['GROUP_ID'], name=g['GROUP_NAME'])
        user_group, _ = BitrixUserGroup.objects.get_or_create(user=user, group=group)
        result.append(user_group)

    return result
