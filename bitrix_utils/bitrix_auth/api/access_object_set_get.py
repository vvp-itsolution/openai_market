# -*- coding: utf-8 -*-

from collections import defaultdict

from django.views.decorators.csrf import csrf_exempt

from its_utils.app_get_params import get_params_from_sources
from its_utils.functions import json_resp
from bitrix_utils.bitrix_auth.functions.bitrix_user_required import bitrix_user_required

from bitrix_utils.bitrix_auth.models import BitrixAccessObject


@csrf_exempt
@get_params_from_sources
@bitrix_user_required
def access_object_set_get(request):

    """
    Получить список объектов, которые относятся к данному правилу
    Возвращает словарь вида {type_id: [ids],}
    """

    set_id = request.its_params.get('id')

    response = defaultdict(list)
    for each in BitrixAccessObject.objects.filter(set_id=set_id):
        response[each.type].append(each.type_id)

    return json_resp(response)
