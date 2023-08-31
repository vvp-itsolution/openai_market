# coding: utf-8


# Default logging for Django. This sends an email to the site admins on every
# HTTP 500 error. Depending on DEBUG, all other log records are either sent to
# the console (DEBUG=True) or discarded by mean of the NullHandler (DEBUG=False).
import optparse
import sys


def get_log_level():
    """
        Функция возвращает значение --log-level= из аргументов скрипта
    """
    for arg in sys.argv:
        arr = arg.split('--log-level=')
        if len(arr) == 2:
            return arr[1]



ITS_UTILS_DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        # 'check_level': {
        #     '()': 'its_utils.app_logging.filter_check_level.FilterCheckLevel',
        # },
    },
    'formatters': {
        'main_formatter': {
            'format': '%(levelname)s:%(name)s: %(message)s '
                     '(%(asctime)s; %(filename)s:%(lineno)d)',
            'datefmt': "%Y-%m-%d %H:%M:%S",
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'null': {
            'class': 'logging.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'its.console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'main_formatter',
        },
        'its.redis': {
            'level': 'DEBUG',
            'class': 'its_utils.app_logging.handlers.RedisHandler',
            'redis_name': 'redis',
            'formatter': 'main_formatter',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
        'django.security': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['console'],
        },
        'its.console': {
            'handlers': ['its.console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'its.redis': {
            'handlers': ['its.redis'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}


def attach_logger(logging_settings, logger_name='', log_level='', arg_looking=True):
    #Если передан в параметрах скрипта лог левел, то переопределям
    arg_log_level = get_log_level()
    if arg_log_level and arg_looking:
        log_level = arg_log_level
    logging_settings['formatters']['main_formatter'] = ITS_UTILS_DEFAULT_LOGGING['formatters']['main_formatter']
    logging_settings['handlers'][logger_name] = ITS_UTILS_DEFAULT_LOGGING['handlers'][logger_name]
    logging_settings['loggers'][logger_name] = ITS_UTILS_DEFAULT_LOGGING['loggers'][logger_name]
    logging_settings['loggers'][logger_name]['level'] = log_level

