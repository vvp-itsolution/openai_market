# -*- coding: utf-8 -*-

from django.utils.http import urlquote

from integration_utils.bitrix24.functions.api_call import (
    api_call,
    convert_params,
    RawStringParam,
    DEFAULT_TIMEOUT,
)
from settings import ilogger


def convert_methods(methods):
    """
    Преобразовать список методов из json в строки, принимаемые методом batch в параметре cmd

    Пример:

    [{
        'crm.lead.list': {
            'filter': {
                'ASSIGNED_BY_ID': 42,
                'STATUS_ID': 1
            }
        },
    }, {
        'crm.deal.list': {
            'filter': {
                'ASSIGNED_BY_ID': 42,
                'STAGE_ID': 2
            }
        }
    }]

    станет:

    [
        'crm.lead.list?filter[ASSIGNED_BY_ID]=42%26filter[STATUS_ID]=1',
        'crm.deal.list?filter[ASSIGNED_BY_ID]=42%26filter[STAGE_ID]=2'
    ]
    """

    cmd = []

    for m in methods:
        method, params = list(m.items())[0]
        cmd.append(RawStringParam(  # RawStringParam - Параметр, к которому не нужно применять urlquote
            '{}?{}'.format(
                method,
                urlquote(convert_params(params), safe='[]=')  # квотировать нужно только &
            )
        ))

    return cmd


def batch_api_call2(domain=None, auth_token=None, methods=None, bitrix_user_token=None, halt=0, timeout=DEFAULT_TIMEOUT):
    """
    Пакетный POST-запрос к Bitrix24 api

    Выполняет все запросы, переданные в methods, в несколько итераций по 50 запросов

    methods - список методов [{"method1": params}, {"method2": params}, ... ]

    timeout - таймаут запроса в секундах NB! если токен протух и производится
        его обновление фактически таймаут может быть в 3 раза больше.

    Есть отличие от batch_api_call:
         результаты будут в списке [res1, res2 ...], а не в словаре {'data_1': res1, 'data_2': res2, ...}

    :return: список результатов или None, если была ошибка
    """

    webhook = False
    if bitrix_user_token:
        domain = getattr(bitrix_user_token, 'domain', None)
        if not domain:
            domain = bitrix_user_token.user.portal.domain

        if bitrix_user_token.web_hook_auth:
            auth_token = bitrix_user_token.web_hook_auth
            webhook = True

        else:
            if getattr(bitrix_user_token.application, 'is_webhook', False):
                auth_token = '{}/{}'.format(bitrix_user_token.user.bitrix_id, bitrix_user_token.auth_token)
                webhook = True

            else:
                auth_token = bitrix_user_token.auth_token

    if not methods:
        methods = {}

    _methods = convert_methods(methods)
    parts_methods = [_methods[i:i + 50] for i in range(0, len(_methods), 50)]  # Получаем список срезов, по 50 штук

    responses = []  # Список ответов и данных

    # Берем по 50 методов и отправляем запросы
    for part in parts_methods:
        response = api_call(
            domain=domain,
            api_method='batch',
            auth_token=auth_token,
            params={
                'cmd': part, 'halt': halt
            },
            webhook=webhook,
            timeout=timeout,
        )

        try:
            data = response.json()

        except ValueError:  # response - не json
            error = True

        else:
            responses.append(data)

            error = data.get('error')
            if error == 'expired_token' and bitrix_user_token and \
                    bitrix_user_token.refresh(timeout=timeout):
                # Если обновление токена прошло успешно, повторить запрос
                return batch_api_call2(domain, auth_token, methods,
                                       bitrix_user_token, halt, timeout)

        if error:
            # Если апи вернуло ошибку, не связанную с токеном, логируем
            ilogger.error(u'bitrix_api_error=>{}'.format(response.text.encode().decode('unicode_escape')))

            return None

    return responses
