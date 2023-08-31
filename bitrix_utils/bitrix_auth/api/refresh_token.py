# -*- coding: utf-8 -*-
from django.views.decorators.csrf import csrf_exempt

from its_utils.app_get_params import get_params_from_sources
from its_utils.functions import json_resp
from bitrix_utils.bitrix_auth.functions.bitrix_user_required import bitrix_user_required


@csrf_exempt
@get_params_from_sources
@bitrix_user_required
def refresh_token(request):
    """ Обновляет токен. Используется в bitrix.patched.js в Базе Знаний
    для обновления токена без айфрейма.
    """
    token = request.bx_user_token
    return json_resp(dict(
        refreshed=token.refresh(),
        AUTH_ID=token.auth_token,
        REFRESH_ID=token.refresh_token,
    ))
