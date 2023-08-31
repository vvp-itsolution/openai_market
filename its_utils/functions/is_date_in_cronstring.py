# -*- coding: utf-8 -*-
import datetime

import pytz
from django.conf import settings
from pytz import UnknownTimeZoneError


def is_date_in_cronstring(dt, cronstring, only_date=False, timezone=None):
    # Принимает дату+время и крон строку
    # Проверяет настал ли момент запуска, если да то возвращает True
    # ВНИМАНИЕ конструкция */5 не реализована пока что #TODO

    """
        >>> from its_utils.functions import is_date_in_cronstring
        >>> from django.utils import timezone
        >>> is_date_in_cronstring(timezone.now(), "1 * * * 4")
        False
    """

    if isinstance(timezone, int):
        # Если часовой пояс передан как смещение от UTC, вычислим timedelta и прибавим к dt
        dt += datetime.timedelta(hours=timezone)

    else:
        if timezone is None and hasattr(settings, 'TIME_ZONE') and settings.TIME_ZONE:
            # Если часовой пояс не передан в параметрах, берём из settings, если указан
            timezone = settings.TIME_ZONE

        if isinstance(timezone, str):
            # конвертируем dt в часовой пояс
            try:
                timezone = pytz.timezone(timezone)
            except UnknownTimeZoneError:
                # если передан неверный часовой пояс, используем UTC
                timezone = pytz.timezone('UTC')

            dt = dt.astimezone(timezone)

    cronparams = cronstring.split(" ")  # "0,2,3 * */5 * *" =>['0,2,3', '*', '*/5', '*', '*']
    if len(cronparams) != 5:
        return False

    minutes = False
    hours = False
    days = False
    months = False
    weekdays = False

    if only_date:
        # Не обращаем внимание на время
        minutes = True
        hours = True
    else:
        if cronparams[0] == '*':
            minutes = True
        elif str(dt.minute) in cronparams[0].split(','):
            minutes = True

        if cronparams[1] == '*':
            hours = True
        elif str(dt.hour) in cronparams[1].split(','):
            hours = True

    if cronparams[2] == '*':
        days = True
    elif str(dt.day) in cronparams[2].split(','):
        days = True

    if cronparams[3] == '*':
        months = True
    elif str(dt.month) in cronparams[3].split(','):
        months = True

    if cronparams[4] == '*':
        weekdays = True
    elif str(dt.weekday() + 1) in cronparams[4].split(','):
        weekdays = True

    # Если все протестировано, то возвращам логическое сложение
    return minutes and hours and days and months and weekdays
