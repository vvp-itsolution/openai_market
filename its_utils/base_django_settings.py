# Обязательные настройки
# это файл надо обязательно влючить в settings.py
# в конце файла
# from its_utils.base_django_settings import check_settings
# check_settings(locals())
# после файла можно что-то переопределить

# Без эксепшна, нефиг без локалсеттингсов проекты делать
import os
import re

from django.utils import timezone

import local_settings
import private_settings

# Переопределяемые настройки

from django.utils.log import DEFAULT_LOGGING
LOGGING = DEFAULT_LOGGING
LOGGING['handlers'].update({
    'django_to_its': {  # Можно назвать как угодно
        'class': 'its_utils.app_logger.its_logger.ItsHandler',
        'filters': ['require_debug_false'],  # Только в продакшне
        'level': 'ERROR',  # только ошибки и критичные
        'log_type': 'server_errors_to_its_logger',  # тип ошибки для логгера
        'exc_info': True,  # опционально, передается в its_logger
    },
})
LOGGING['loggers'].update({
    'django': {
        'level': 'ERROR',  # Только ошибки
        'handlers': [
            'console',  # В консоль в dev-окружении
            'django_to_its',  # в its_logger+телегу на проде
            'mail_admins',  # на почту на проде
        ],
    },
})


REQUIRED_INSTALLED_APPS = [
    'its_utils.app_check_django_project',
    'its_utils.app_logger',
    'its_utils.app_cron',
    'its_utils.app_gitpull',
    'its_utils.app_error',
    'its_utils.app_settings',
    'its_utils.app_admin',
    ]


class SettingsMetaClass:
    LANGUAGE_CODE = 'ru-ru'

def check_settings(settings):
    # override settings from local_settings.py
    for item in dir(local_settings):
        if item.startswith("__"):
            continue
        settings[item] = getattr(local_settings, item)

    # override settings from private_settings.py
    for item in dir(private_settings):
        if item.startswith("__"):
            continue
        settings[item] = getattr(private_settings, item)

    settings['DJANGO_STARTED'] = timezone.now()

    settings['LOGGING'] = LOGGING
    settings['INSTALLED_APPS'] = settings['INSTALLED_APPS'] + REQUIRED_INSTALLED_APPS
    if 'integration_utils.its_utils.app_gitpull' in settings['INSTALLED_APPS'] and 'its_utils.app_gitpull' in settings['INSTALLED_APPS']:
        settings['INSTALLED_APPS'].remove('its_utils.app_gitpull')
    if 'integration_utils.its_utils.app_settings' in settings['INSTALLED_APPS'] and 'its_utils.app_settings' in settings['INSTALLED_APPS']:
        settings['INSTALLED_APPS'].remove('its_utils.app_settings')

    #Подключаем статик файлы
    # settings['STATIC_URL'] = '/static/'
    # settings['STATICFILES_DIRS'] = [
    #     os.path.join(settings['BASE_DIR'], "static"),
    # ]
    settings['ITS_COLLECT_STATIC'] = True


    from its_utils.app_logger.its_logger import ItsLogger
    settings['ilogger'] = ItsLogger()

    from django.conf.locale.ru import formats as ru_formats
    ru_formats.DATETIME_FORMAT = "d.m.Y H:i:s"

    if not 'DOMAIN' in settings:
        raise Exception('Не задан DOMAIN')

    if not 'ITS_LOGGER_TELEGRAM_CHAT' in settings:
        raise Exception('Не задан ITS_LOGGER_TELEGRAM_CHAT если не знаете что писать то -362379873')

    if not 'EMAIL_HOST' in settings:
        raise Exception('Не задан EMAIL_HOST (обычно localhost)')

    if not 'EMAIL_HOST_USER' in settings:
        raise Exception('Не задан EMAIL_HOST_USER (обычно "")')

    if not 'EMAIL_HOST_PASSWORD' in settings:
        raise Exception('Не задан EMAIL_HOST_PASSWORD (обычно "")')

    if not 'SERVER_EMAIL' in settings:
        raise Exception('Не задан SERVER_EMAIL (обычно PROJECT_NAME@it-solution.ru)')

    if not 'MEDIA_ROOT' in settings or not 'MEDIA_URL' in settings:
        raise Exception("Не заданы MEDIA_ROOT и/или MEDIA_URL (обычно import os _PATH = os.path.abspath(os.path.dirname(__file__)) MEDIA_ROOT = os.path.join(_PATH, 'media') MEDIA_URL = 'media/'")

    with open(os.path.join(settings['BASE_DIR'], 'urls.py'), 'r') as file:
        urls_content = file.read()
        if not re.search('^base_urls\(locals\(\)\)', urls_content, re.MULTILINE):
            # Проверяем добавлен ли base_urls
            # Должно быть в файле urls
            # from its_utils.base_urls import base_urls
            # base_urls(locals())
            raise Exception('Не подключен base_urls')


    settings['CHECK_SETTINGS_INCLUDED'] = True