# -*- coding: UTF-8 -*-

import requests
from django.conf import settings


def entry_to_ticket(ticket_id, text, api_key=None, timeout=2):

    """
    Добавить пост с текстом text в тикет с нормером ticket_id.
    timeout определяет сколько секунд функция будет ждать ответа на запрос.
    API_KEY берется сначала из параметров (если есть), потом из настроек (переменная TICKETS_API_KEY),
    а если ни того, ни другого не было, то используется стандартный.
    Возвращает статус и текст ошибки/ответа
    """

    api_key = api_key or getattr(settings, 'TICKETS_API_KEY', '123123')
    url = 'https://tsapi.it-solution.ru/api/v2/entry.new/?api_key=%s' % api_key
    try:
        response = requests.post(url, {'text': text, 'ticket_id': ticket_id}, timeout=timeout)
    except requests.exceptions.RequestException as e:
        code, response_text = 500, e
    else:
        code, response_text = response.status_code, response.reason

    return code, response_text
