import time
from datetime import datetime

from django_redis import get_redis_connection

from settings import ilogger


def throttling_check(key, count, interval):
    """
    https://ts.it-solution.ru/#/ticket/60230/

    Функция служит для ограничения количества запросов за интервал времени.

    Для примера допустим, что у нас есть функция do_something, которую мы можем вызывать не более ста раз в минуту.
    С помощью throttling_check мы можем следить, чтобы она не выполнялась чаще:

    if throttling_check('do_something', 100, 60):
        # Функция была вызвана менее 100 раз за последнюю минуту - можно вызвать ещё раз
        do_something()

    else:
        # Пытаемся выполнить больше 100 вызовов за 60 секунд - обработать эту ситуацию
        ...

    Для подсчета времени используется список с временными отметками длинной count
    [12:00:01, 12:00:01, 12:00:04, 12:00:05]


    :param key: ключ для потока
    :param count: количество за интервал
    :param interval: итервал в секундах
    :return: True, если ограничение не превышено, иначе - False
    """

    redis = get_redis_connection()

    # Получить время когда был вызван метод count раз назад
    # если count = 1, то предыдущий раз был в ...
    first_request_time = redis.lindex(key, count-1)
    new_request_time = datetime.now()

    if first_request_time is not None:
        first_request_time = datetime.fromtimestamp(float(first_request_time))
        delay = (first_request_time - new_request_time).total_seconds() + interval
        if delay > 0:
            #ilogger.warning('throttling_check', '{}: {} seconds left'.format(key, delay))
            return False

    # Вставляем в начало списка время последнего запроса
    redis.lpush(key, time.mktime(new_request_time.timetuple()))

    # Чистим список = Оставляем в массиве только count элементов
    redis.ltrim(key, 0, count-1)


    return True
