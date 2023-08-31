# -*- coding: UTF-8 -*-

from django.db import models

from bitrix_utils.bitrix_auth.models import BitrixAccessObject


def has_access(user, set_id, app_name=None):
    """
    Проверяет имеет ли пользователь отношение к данному разрешению
    """

    groups, departments = user.get_groups_and_departments(app_name=app_name)

    query = (models.Q(type=BitrixAccessObject.USER, type_id=user.bitrix_id) |
             models.Q(type=BitrixAccessObject.GROUP, type_id__in=groups) |
             models.Q(type=BitrixAccessObject.DEPARTMENT, type_id__in=departments) |
             models.Q(type=BitrixAccessObject.SYSTEM_GROUP, type_id=BitrixAccessObject.ALL_USERS))

    return bool(BitrixAccessObject.objects.filter(query, set_id=set_id))
