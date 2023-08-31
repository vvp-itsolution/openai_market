# -*- coding: UTF-8 -*-

import requests
from django.conf import settings


def create_ticket(api_key=None, timeout=2, **kwargs):

    """
    Создать новый тикет. Обязательные параметры: api_key, project_id, name, users
    Причем users - строка, список id пользователей через запятую
    Остальные параметры повторяют названия полей из класса Ticket с некоторыми особенностями
    - не записываются m2m поля
    - все ForeignKey поля должны быть предоставлены с суффиксом _id, например with_ball_id
    - date/datetime поля должны быть в формате ISO
    """

    api_key = api_key or getattr(settings, 'TICKETS_API_KEY', '123123123')
    url = 'https://tsapi.it-solution.ru/api/v2/ticket.new/?api_key=%s' % api_key

    for key in 'author_id', 'project_id', 'name', 'users', 'responsible_id', 'with_ball_id':
        try:
            kwargs[key]
        except KeyError as e:
            return 500, u'%s is mandatory argument' % e

    try:
        response = requests.post(url, json=kwargs, timeout=timeout)
    except requests.exceptions.RequestException as e:
        code, response_text = 500, e
    else:
        code, response_text = response.status_code, response.text

    return code, response_text
