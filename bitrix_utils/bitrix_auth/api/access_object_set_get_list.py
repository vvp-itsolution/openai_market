# -*- coding: utf-8 -*-

from django.views.decorators.csrf import csrf_exempt

from its_utils.app_get_params import get_params_from_sources
from its_utils.functions import json_resp
from bitrix_utils.bitrix_auth.functions.bitrix_user_required import bitrix_user_required
from bitrix_utils.bitrix_auth.functions.get_access_list import get_access_list


@csrf_exempt
@get_params_from_sources
@bitrix_user_required
def access_object_set_get_list(request):
    """
    Возвращает список правил, в которых участвует данный пользователь
    """

    return json_resp(get_access_list(request.bx_user, app_name=['itsolutionru.kdb', 'itsolutionru.kdbwithoutlogo']))
