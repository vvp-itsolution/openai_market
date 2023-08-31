# -*- coding: utf-8 -*-
import logging
import json
from django.conf import settings
from django.utils import timezone
from django_redis import get_redis_connection
from its_utils.app_logging.models import LogFromRedis, LoggedScript, LogType
from its_utils.app_logging.handlers import RedisHandler
from django.core.mail import mail_admins
from dateutil.parser import parse

TRUNCATE_SETTINGS_PARAM = 'TIME_FOR_TRUNCATE_APP_LOGGING'
DEFAULT_TRUNCATE_CRON_STRING = '0 1 * * *'


def _get_handlers_settings():
    try:
        # python 2
        to_iter = logging.Logger.manager.loggerDict.itervalues()
    except:
        # python 3
        to_iter = logging.Logger.manager.loggerDict.values()

    for logger in to_iter:
        for handler in getattr(logger, 'handlers', []):
            if isinstance(handler, RedisHandler):
                yield handler.redis_name, handler.q_name


def clean_and_count_logs():
    """
    Удалить устаревшие записи, посчитать количество
    """

    res = []
    for lt in LogType.objects.all():
        lt.clean_logs()
        count = lt.count_logs()
        res.append(u'{type}: {count}'.format(type=lt.name, count=count))

    return u'\n'.join(res)


NUL_SYMBOL = '\\x00'


def delete_nul_symbols(string):
    """
    Возникла ошибка ValueError: A string literal cannot contain NUL (0x00) characters
    Чтобы её избежать будем удалять NUL-символ из сообщения лога
    """
    return u''.join(list(filter(lambda c: c != NUL_SYMBOL, string)))


def handle_redis_logs():
    """
    Забирает из редиса логи, шлет на почту, пишет в базу
    """
    # берём настройки логирования скриптов
    logged_scripts = dict((script.pathname, script) for script in LoggedScript.objects.all())
    logged_types = dict((log_type.name, log_type) for log_type in LogType.objects.all())

    for redis_name, q_name in set(_get_handlers_settings()):
        redis = get_redis_connection(redis_name)

        log_counts = {50: 0,
                      40: 0,
                      30: 0,
                      20: 0,
                      10: 0,
                      0: 0}

        logs_to_save = []
        logs_to_email = []
        count = 0
        while True and count < 2000:
            log = redis.rpop(q_name)
            if not log:
                break

            count += count

            try:
                log = json.loads(log.decode('utf-8'))
            except (ValueError, OverflowError, TypeError):
                log = {
                    'name': 'error in logging',
                    'level': 50,
                    'pathname': 'error in logging',
                    'lineno': 0,
                    'msg': 'error in logging',
                    'exception': 'error in logging',
                }
            pathname = log['pathname'] or ''
            level = log['level'] or -1

            # Значение, которые укажут сохранять или отправлять логи
            # По умолчанию все отправляется,
            # но все условия умножаются через and, так что
            # если в logged_script или в log_type сказано, что не надо, то ничего не происходит
            save_to_db = send_email = True

            # Проверем указан ли тип события
            _ = log['msg'].split('=>')
            if len(_) > 1:
                log_msg_type = _[0][:255]
            else:
                log_msg_type = 0

            log_type = None
            if log_msg_type:
                log_type = logged_types.get(log_msg_type)
                if not log_type:
                    # такого типа нет в базе, создаём
                    log_type = LogType.objects.create(name=log_msg_type)
                    logged_types[log_msg_type] = log_type

                save_to_db = save_to_db and level >= log_type.level_save_to_db
                send_email = send_email and level >= log_type.level_send_email

            if pathname:
                # путь к скрипту дан
                script = logged_scripts.get(pathname)
                if not script:
                    # скрипта нет в базе, создаём
                    script = LoggedScript.objects.create(pathname=pathname)
                    logged_scripts[pathname] = script
                save_to_db = save_to_db and level >= script.level_save_to_db
                send_email = send_email and level >= script.level_send_email

            if save_to_db or send_email:
                # пытаемся получить строку datetime из лога
                dt_str = log.get('dt', None)
                # если удалось, то парсим в объект datetime
                if dt_str:
                    dt = parse(dt_str)
                # если не удалось, то подставляем текущий datetime
                else:
                    dt = timezone.now()

                db_log = LogFromRedis(
                    name=delete_nul_symbols(log['name']),
                    level=level,
                    pathname=pathname,
                    lineno=log['lineno'] or -1,
                    msg=delete_nul_symbols(log['msg']) or '',
                    dt=dt,
                    exception=log['exception'] or '',
                    type=log_type
                )
            if save_to_db:
                logs_to_save.append(db_log)
            if send_email:
                log_counts[db_log.level] += 1
                logs_to_email.append(db_log)

        subject = ''
        if logs_to_email:

            most_critical = 0
            levels_list = ''
            for counter in log_counts:
                if log_counts[counter]:
                    levels_list += '{}: {}'.format(logging.getLevelName(counter), log_counts[counter]) + '\n'

                    if most_critical < counter:
                        most_critical = counter

            subject = u'[app_logging %s] most_critical %s' % (settings.DOMAIN, logging.getLevelName(most_critical))

            message = 'http://%s/admin/app_logging/logfromredis/ \n\n' % settings.DOMAIN + \
                      levels_list + '\n' + '\n\n'.join(log.pretty_message for log in logs_to_email)
            mail_admins(subject, message, fail_silently=True)
        if logs_to_save:
            LogFromRedis.objects.bulk_create(logs_to_save)

        # Запуск очистки логов
        from its_utils.functions import is_date_in_cronstring
        truncate_cron_string = getattr(settings, TRUNCATE_SETTINGS_PARAM, DEFAULT_TRUNCATE_CRON_STRING)
        if is_date_in_cronstring(timezone.now(), truncate_cron_string):
            clean_and_count_logs()

        return u'всего %s  -- %s' % (len(logs_to_save), subject)
