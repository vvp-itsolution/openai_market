import logging


class ItsHandler(logging.Handler):
    """Эта штуковина нужна для переадресации ошибок джанго-логгера в итс-логгер,
    Например данная конфа будет отправлять ошибки сервера в its_logger
    и соответственно постить их в телеграм:

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
    """
    def __init__(self, log_type, exc_info=False, level=logging.NOTSET):
        # type: (int, bool, int) -> None
        super(ItsHandler, self).__init__(level=level)
        self.log_type = log_type
        self.exc_info = exc_info

    def emit(self, record):
        request = None

        try:
            from settings import ilogger
            """
            Ожидается ошибка в таком виде, НАДО взять 1 и последнюю строки
            
            Internal Server Error: /api/v1/froala/disk_file_proxy/4016/187/
            Traceback (most recent call last):
              File "/home/kdb/env_kdb/lib/python3.5/site-packages/django/core/handlers/exception.py", line 34, in inner
                response = get_response(request)
              File "/home/kdb/env_kdb/lib/python3.5/site-packages/django/core/handlers/base.py", line 115, in _get_response
                response = self.process_exception_by_middleware(e, request)
              File "/home/kdb/env_kdb/lib/python3.5/site-packages/django/core/handlers/base.py", line 113, in _get_response
                response = wrapped_callback(request, *callback_args, **callback_kwargs)
              File "/home/kdb/env_kdb/lib/python3.5/site-packages/newrelic/hooks/framework_django.py", line 544, in wrapper
                return wrapped(*args, **kwargs)
              File "/home/kdb/kdb/articles/api/froala/disk_file_proxy.py", line 104, in disk_file_proxy
                is_admin=None,
              File "/home/kdb/kdb/bitrix_utils/bitrix_auth/models/bitrix_user_token.py", line 324, in get_random_token_for_apps
                .format(application_names, portal_id)
            bitrix_utils.bitrix_auth.models.bitrix_user_token.BitrixUserToken.DoesNotExist: application_name: ['itsolutionru.kdb', 'itsolutionru.kdbpremium'], portal_id: 4016
            """
            msg_arr = self.format(record).split("\n")
            msg = "{}\n{}".format(msg_arr[0], msg_arr[-1])
            request = getattr(record, 'request', None)
            record = ilogger.log(self.level, self.log_type, msg, exc_info=self.exc_info, request=request)
            if record:
                request.session['log_record_id'] = record.id

        except Exception as exc:
            ilogger.warning(
                'error_500_handle_fail',
                'ошибка 500! смотрите трейсбек на почте, т.к не удалось сохранить в БД ({})\n{}'.format(
                    exc, '\n'.join('{}: {}'.format(k, v) for k, v in request.META.items()) if request else 'no request'
                ),
            )

            self.handleError(record)
