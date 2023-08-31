# -*- coding: utf-8 -*-
from functools import wraps

import six

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from bitrix_utils.bitrix_auth.models import BitrixUser, BitrixUserToken

if False:
    from typing import Tuple


def _validate_token(http_auth_token):  # type: (str) -> None
    try:
        pk, token = http_auth_token.split('::') if http_auth_token else ('', '')
    except ValueError as e:
        six.raise_from(ValueError('invalid auth token'), e)
    else:
        if not all((pk, token)) or not pk.isdigit():
            raise ValueError('invalid auth token')


def _authenticate(request):  # type: (HttpRequest) -> Tuple[BitrixUser, BitrixUserToken]
    """В каждом запросе установлен заголовок HTTP_AUTHORIZATION,
    установку см. в README
    """
    # Авторизация секретом (притвориться пользователем)
    shs = request.GET.get('shs')
    token_id = request.GET.get('token_id')
    # Авторизация заголовком
    http_auth_token = request.META.get('HTTP_AUTHORIZATION')

    bx_user_token = None
    if shs == settings.BITRIX_SHADOW_SECRET and token_id:
        # Авторизация секретом в приоритете
        bx_user_token = BitrixUserToken.objects \
            .select_related('user') \
            .get(pk=int(token_id))
    elif http_auth_token:
        _validate_token(http_auth_token)
        bx_user_token = BitrixUserToken.get_by_token(http_auth_token)

    bx_user = bx_user_token and bx_user_token.user
    return bx_user, bx_user_token


def bitrix_user_required(func):
    """Авторизация Bitrix-пользователя заголовком аторизации
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            bx_user, bx_user_token = _authenticate(request)
        except ValueError as e:
            return HttpResponse('Unauthorized: %s' % e, status=401)
        if bx_user is None:
            return HttpResponse('Unauthorized', status=401)

        request.bx_user = bx_user
        request.bx_user_token = bx_user_token
        return func(request, *args, **kwargs)

    return wrapper


def bitrix_user_optional(func):
    """Опциональная авторизация битрикс-пользователя заголовком авторизации,
    если заголовок авторизации не представлен, request.bx_user
    и request.bx_user_token устанавливаются None
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            request.bx_user, request.bx_user_token = _authenticate(request)
        except ValueError as e:
            return HttpResponse('Unauthorized: %s' % e, status=401)
        return func(request, *args, **kwargs)
    return wrapper
