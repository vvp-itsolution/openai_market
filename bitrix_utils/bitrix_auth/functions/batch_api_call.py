# -*- coding: utf-8 -*-
from bitrix_utils.bitrix_auth.functions.api_call2 import call_with_fall_to_http

from settings import ilogger
from ._log import log_bitrix_request, log_bitrix_response


def convert_params(form_data):
    """
    Это слегка измененный метод из api_call.py.
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
            return '%s=%s' % (key, values)

        for k, v in iterable:
            if key is not None:
                k = '%s[%s]' % (key, k)
            result = recursive_traverse(v, k)
            if isinstance(result, list):
                params.append('%26'.join(result))
            else:
                params.append(result)

        return params

    # Bitrix требует, чтобы поле "TITLE" для лида было первым параметром,
    # поэтому переставляем его в начало списка параметров
    # По умолчанию TITLE в конце списка, почему(?)
    data = recursive_traverse(form_data)

    # Что-то очень странное
    # ---------------------------------------------------------
    # data = data[0].split("&")
    # title = data.pop()  # Удаляем последний элемент списка
    # data.insert(0, title)
    # ---------------------------------------------------------

    s = '%26'.join(data)
    return s


# Обрабатываем полученные параметры в виде списка словарей методов для Batch-вызова
# [{'имя метода': 'параметры метода'}, {...}, {...}]
def params_converse(data, names=None):
    params = []
    n = 0

    for method in data:  # Для кажого элемента списка
        for key, value in method.items():  # где каждый элемент - словарь, создадим строку для URL
            if names:
                data_key = names[n]
            else:
                data_key = 'data_{}'.format(n)
            if not value:  # У метода нет параметров
                result = "cmd[%s]=%s" % (data_key, key)
            else:
                # Есть разница между & и %26. & мы разделяем параметры,
                # а %26 - подпараметры внутри параметров
                result = "cmd[{command_name}]={method_name}%3F{params}".format(
                    command_name=data_key,
                    method_name=key,
                    params=convert_params(value),
                )
            n += 1  # Просто счетчик для имени массива результата data, который вернет Bitrix
            params.append(result)

    return "&".join(params)  # join объединяет все элементы массива и пишет между ними знак &


def batch_api_call(domain, auth_token, methods, bitrix_user_token=None, halt=0, webhook=False, method_names=None):
    """
    Пакетный POST-запрос к Bitrix24 api
    За раз можно отправить до 50 запросов
    В настоящее время проверялся только на crm.lead.add и user.current
    За остальные методы не ручаюсь
    ВНИМАНИЕ: знаки &, ?, = и т.д. в URL кодируются символами, где
    & = %26, ?=%3F, и т.д.

    webhook: Метода вызывается через webhook. auth_token в этом случае - "{bitrix_id пользователя}/{ключ webhook'а}"
    если bitrix_user_token.application - это webhook, параметр webhook игнорируется

    method_names: список названий методов, для обращениея через '$result[some_method][FIELD]'

    СТРОКА:  cmd[add_lead_1]=crm.lead.add?%26fields[TITLE]=TEST 1%26fields[NAME]=PAVEL&cmd[add_lead_2]=crm.lead.add?%26fields[TITLE]=TEST 2%26fields[NAME]=IGOR
    """

    if bitrix_user_token:
        if bitrix_user_token.application.is_webhook:
            webhook = True
            auth_token = '{}/{}'.format(bitrix_user_token.user.bitrix_id, bitrix_user_token.auth_token)

        else:
            auth_token = bitrix_user_token.auth_token

    if not methods:
        methods = {}

    parts_methods = [methods[i:i + 50] for i in range(0, len(methods), 50)]  # Получаем список срезов, по 50 штук
    if method_names is not None:
        assert len(method_names) == len(methods)
        parts_method_names = [method_names[i:i + 50] for i in range(0, len(method_names), 50)]
    else:
        parts_method_names = [None] * len(parts_methods)

    responses = []  # Список ответов и данных

    hook_key = ''
    if webhook:
        hook_key = '{}/'.format(auth_token)

    url = 'https://{}/rest/{}batch.json'.format(domain, hook_key)
    batch_params = "{}halt={}&".format("" if webhook else "auth={}&".format(auth_token), halt)

    # Берем первые 50 методов и отправляем запрос
    for part, names_part in zip(parts_methods, parts_method_names):
        converted_params = params_converse(part, names_part)
        converted_params = batch_params + converted_params  # halt=0 - не прерывает запрос в случае ошибки

        converted_params = converted_params.encode("utf-8")

        log_bitrix_request(
            caller='batch_api_call',
            http_method='POST',
            method='batch',
            params=dict(
                common_batch_params=batch_params,
                batch_params=part,
                batch_params_names=names_part,
                converted=converted_params,
            ),
            portal_domain=domain,
            auth_token=hook_key if webhook else auth_token,
            url=url,
            bx_user=bitrix_user_token and bitrix_user_token.user,
            bx_user_token=bitrix_user_token,
        )
        response = call_with_fall_to_http(url, converted_params)
        log_bitrix_response(
            caller='batch_api_call',
            http_method='POST',
            method='batch',
            params=dict(
                common_batch_params=batch_params,
                batch_params=part,
                batch_params_names=names_part,
                converted=converted_params,
            ),
            portal_domain=domain,
            auth_token=hook_key if webhook else auth_token,
            url=url,
            bx_user=bitrix_user_token and bitrix_user_token.user,
            bx_user_token=bitrix_user_token,
            requests_response=response,
        )

        try:
            data = response.json()
            responses.append(data)
        except ValueError:
            ilogger.exception('ValueError')
            responses.append({"text": response.text, "status": response.status_code})
            return response.text, response.status_code

        # Нужна ли мне выдача информации об ошибке по токену, как исключение?
        if data.get('error'):
            if data['error'] == 'expired_token' and bitrix_user_token:
                success = bitrix_user_token.refresh()
                if success:
                    # Если обновление токена прошло успешно, повторить запрос
                    return batch_api_call(domain, bitrix_user_token.auth_token, methods)
                else:
                    raise RuntimeError('could not refresh token')
            else:
                # Если апи вернуло ошибку, не связанную с токеном, логируем
                ilogger.error(u'bitrix_api_error=>{}'.format(response.text.encode().decode('unicode_escape')))

    return responses
