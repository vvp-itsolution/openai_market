# -*- coding: UTF-8 -*-

from django.db import models

from bitrix_utils.bitrix_auth.models import BitrixAccessObject


def get_access_list(user, app_name=None):
    """
    Возвращает список правил, в которых участвует данный пользователь
    """

    groups, departments = user.get_groups_and_departments(app_name=app_name)

    query = (models.Q(type=BitrixAccessObject.GROUP, type_id__in=groups) |
             models.Q(type=BitrixAccessObject.DEPARTMENT, type_id__in=departments) |
             models.Q(type=BitrixAccessObject.USER, type_id=user.bitrix_id) |
             models.Q(type=BitrixAccessObject.SYSTEM_GROUP, type_id=BitrixAccessObject.ALL_USERS))

    return list(BitrixAccessObject.objects.values_list('set_id', flat=True).filter(query))
