# coding: utf-8
import logging


class MailFilterLimitToSend(logging.Filter):
    """Фильтр писем на почту, отправляет не более max_errors штук в max_time секунд

    ДЛЯ КОРРЕКТНОЙ РАБОТЫ НЕОБХОДИМО В settings.CACHES добавить cache с названием redis
    """
    max_errors = 3
    max_time = 10

    def filter(self, record):
        from django_redis import get_redis_connection
        redis = get_redis_connection("redis")
        # пробуем достать количество логов которое мы отправили за последние max_time секунд
        count = redis.get('errors_sent')
        # если значения нет, то
        if not count:
            # ставим единицу, так как это первый лог и редис не умеет в дефолтные значения
            redis.set('errors_sent', 1)
            redis.expire('errors_sent', self.max_time)
        else:
            # если значение есть, то переводим строку в число
            count = int(count)
            # если мы отправили логов меньше за последние max_time секунд чем max_errors
            if count < self.max_errors:
                # то записываем новон значение в редис
                redis.set('errors_sent', str(count+1))
                redis.expire('errors_sent', self.max_time)
        # возвращаем True если мы отправили логов меньше за последние max_time секунд чем max_errors, иначе False
        result = count < self.max_errors
        #redis.set('aaaaaaa', result)
        #print result
        return result
