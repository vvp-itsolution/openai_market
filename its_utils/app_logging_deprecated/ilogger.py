# -*- coding: utf-8 -*-
import json
import logging
import traceback

from django.utils import timezone


class ILogger():
    # Пишет лог в редис, потом по крону письма с логами
    # отправляются админам и логи пишутся в базу

    def __init__(self, redis_name, q_name='its_logging.log',
                 limit=10000, level=logging.NOTSET):
        assert limit > 0
        self.redis_name = redis_name
        from django.conf import settings
        self.q_name = "{}.{}".format(getattr(settings, 'ITS_LOG_PREFIX', ''), q_name)
        self.limit = limit

    def error(self):
        # Заготовка
        pass

    def emit(self, record):
        from django_redis import get_redis_connection
        from django.core.serializers.json import DjangoJSONEncoder
        # record: https://docs.python.org/2/library/logging.html#logrecord-objects
        exception = None
        if record.exc_info:
            exception = ''.join(traceback.format_exception(*record.exc_info))

        record_data = {
            'name': record.name,
            'level': record.levelno,
            'pathname': record.pathname,
            'lineno': record.lineno,
            'msg': record.msg,
            'dt': timezone.now(),
            'exception': exception,
        }
        redis = get_redis_connection(self.redis_name)
        q_len = redis.lpush(self.q_name, json.dumps(record_data, cls=DjangoJSONEncoder))
        # Если очередь логов на создание превысила лимит,
        # значит мы либо слишком много делаем логов либо
        # у нас не запущен крон обрабатывающий логи
        overflow = q_len - self.limit
        if overflow > 0:
            # NB! В редис *range-, *trim- и подобные методы
            # включают конечный индекс
            # (например "LRANGE 0 2" вернет первые 3 элемента)
            # см. http://redis.io/commands/ltrim
            redis.ltrim(self.q_name, 0, self.limit - 1)  # Оставляет только {self.limit} элементов
