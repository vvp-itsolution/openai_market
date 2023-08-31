# coding: utf-8

from django.conf import settings

DEFAULT_APP_SETTINGS = dict(
    # АйДи чата телеграм куда будут отправляться сообщения
    ITS_LOGGER_TELEGRAM_CHAT=None,

    # Будет упоминать юзера при ошибках уровня Error и Critical
    ITS_LOGGER_TELEGRAM_ERROR_TAG='@hlopikit',

    # Асинхронная отправка логов в телеграм
    ITS_LOGGER_TELEGRAM_ASYNC=True,
)


def get_setting(setting):
    return getattr(settings, setting, DEFAULT_APP_SETTINGS.get(setting, None))
