# -*- coding: utf-8 -*-
import requests
from django.conf import settings

from bitrix_utils.bitrix_auth.models import BitrixUser
from ._log import log_bitrix_request, log_bitrix_response


def convert_params(form_data):

    """
    Рекурсивно, с помощью функции recursive_traverse проходит словарь/кортеж/список,
    превращая его в параметры, понятные битриксу.

    {field: {hello: 'world'}} превратится в 'field[hello]=world'
    [{field: hello}, {field: world}] => '0[field]=hello&1[field]=world'
    {auth: 123, field: {hello: world}} => 'auth=123&field[hello]=world'
    и т.д.
    """

    def recursive_traverse(values, key=None):

        """
        При первом вызове key ничему не равен, затем к нему будут добавляться новые ключи.
        '' => 'field' => 'field[hello]' => 'field[hello][there]' => ...

        Если values - строка, то возвращается строка вида 'key=values', иначе в список собираются такие же ключи и
        собираются в строку вида 'key=value&key=value' и т.д.
        """

        params = []
        if isinstance(values, dict):
            iterable = values.items()
        elif isinstance(values, (list, tuple)):
            iterable = enumerate(values)
        else:
            return u'%s=%s' % (key, values)

        for k, v in iterable:
            if key is not None:
                k = u'%s[%s]' % (key, k)
            result = recursive_traverse(v, k)
            if isinstance(result, list):
                params.append(u'&'.join(result))
            else:
                params.append(result)

        return params

    return u'&'.join(recursive_traverse(form_data))


def api_call(domain, api_method, auth_token, params=None, old_try_to_refresh=True):

    """
    POST-запрос к Bitrix24 api
    domain: Полный адрес домена (it-solution.bitrix24.ru)
    api_method: Имя метода (task.item.add)
    auth_token: Токен пользователя
    params: Словарь параметров. Может содержать просто ключ-значение, либо списки, кортежи или опять словари.
    Все это может быть перемешано.

    Возвращает данные в JSON формате и статус или ответ как есть и статус, если произошла ошибка на сервере битрикса
    """

    if not params:
        params = {}

    params['auth'] = auth_token

    converted_params = convert_params(params).encode('utf-8')
    url = 'https://{}/rest/{}.json'.format(domain, api_method)

    log_bitrix_request(
        caller='api_call',
        http_method='POST',
        method=api_method,
        params=dict(
            py=params,
            encoded=converted_params,
        ),
        portal_domain=domain,
        auth_token=auth_token,
        url=url,
    )

    response = requests.post(
        url, converted_params,
        auth=getattr(settings, 'B24_HTTP_BASIC_AUTH', None),
    )

    log_bitrix_response(
        caller='api_call',
        http_method='POST',
        method=api_method,
        params=dict(
            py=params,
            encoded=converted_params,
        ),
        portal_domain=domain,
        auth_token=auth_token,
        url=url,
        requests_response=response,
    )

    try:
        data = response.json()
    except ValueError:
        return response.text, response.status_code

    if data.get('error'):
        if data['error'] == 'expired_token' and old_try_to_refresh:
            bu = BitrixUser.objects.get(auth_token=auth_token)
            success = bu.refresh_auth_token()
            if success:
                # Если обновление токена прошло успешно, повторить запрос
                return api_call(domain, api_method, bu.auth_token, params)

    return data, response.status_code
