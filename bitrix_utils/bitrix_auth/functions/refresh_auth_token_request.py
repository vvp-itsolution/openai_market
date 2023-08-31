# -*- coding: utf-8 -*-

import logging

import requests

from django.conf import settings

from bitrix_utils.bitrix_auth.models import BitrixUser
from settings import ilogger


def refresh_auth_token_request(portal_domain, refresh_token):
    """
    Выполняет запрос на обновление токена
    portal_domain = 'it-solution.bitrix.ru'
    refresh_token = 'fewweufhuwehfuhweufhweiufh'

    возвращает:
    Статус зароса, объект response
    """

    # по умолчанию берем настройки из сеттинга
    bitrix_client_id = settings.BITRIX_CLIENT_ID
    bitrix_client_secret = settings.BITRIX_CLIENT_SECRET

    try:
        # если нашли пользователя, берем настройки, сохраненные для него

        bu = BitrixUser.objects.get(portal__domain=portal_domain, refresh_token=refresh_token)
        app = bu.application

        if app:
            bitrix_client_id = app.bitrix_client_id
            bitrix_client_secret = app.bitrix_client_secret
    except BitrixUser.DoesNotExist:
        pass

    params = {
        'grant_type': 'refresh_token',
        'client_id': bitrix_client_id,
        'client_secret': bitrix_client_secret,
        'refresh_token': refresh_token,

        # 'scope': settings.BITRIX_SCOPE,
        # 'redirect_uri': settings.BITRIX_REDIRECT_URL,
    }
    params = '&'.join(['{}={}'.format(k, v) for k, v in params.items()])
    url = 'https://oauth.bitrix.info/oauth/token/?{}'.format(params)
    response = requests.get(url, auth=getattr(settings, 'B24_HTTP_BASIC_AUTH', None))



    if response.status_code >= 500:
        ilogger.warning(u'refresh_token_error=>{} {} -> {}'.format(url, params, response.text))
        return False, response

    response_json = response.json()
    if response_json.get('error'):
        ilogger.warning(u'refresh_token_error=>{} {} -> {}'.format(url, params, response.text))
        return False, response

    ilogger.info(u'refresh_token=>{} {} -> {}'.format(url, params, response.text))

    return True, response
