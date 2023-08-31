# -*- coding: utf-8 -*-

from bitrix_utils.bitrix_auth.functions.batch_api_call import batch_api_call
from bitrix_utils.bitrix_auth.functions.update_groups import update_groups
from bitrix_utils.bitrix_auth.functions.update_departments import update_departments

from bitrix_utils.bitrix_auth.models import BitrixUser


def update_portal_info(portal):

    """
    Для данного портала обновить список социальных групп и отделов.
    Возвращает словарь из двух элменетов - списков созданных/обновленных объектов
    """

    departments, groups = None, None
    for user in BitrixUser.objects.filter(portal=portal):
        response = batch_api_call(portal.domain, user.auth_token, [{'department.get': None}, {'sonet_group.get': None}])[0]
        if isinstance(response, dict) and \
                not response.get('result_error') and \
                not response.get('error'):
            departments = response['result']['result'].get('data_0')
            groups = response['result']['result'].get('data_1')
            break

    result = {'groups': [], 'departments': []}

    if groups:
        result['groups'] = update_groups(portal, groups)

    if departments:
        result['departments'] = update_departments(portal, departments)

    return result
