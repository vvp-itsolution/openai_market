# coding: utf-8

import inspect
import pprint
import sys
import traceback

from django.conf import settings
from django.core.mail import mail_admins
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from its_utils.app_cron.cron_thread_local import append_cron_result
from its_utils.app_logger import app_settings
from its_utils.app_logger.its_logger.LocalExceptionReporter import LocalExceptionReporter
from its_utils.app_logger.its_logger.logger_thread_local import get_request_start_time
from its_utils.app_telegram_post.post_to_telegram import post_to_telegram, post_to_telegram_async
from its_utils.functions import make_chunks
from its_utils.app_logger.utils import log_levels

PYTHON_VERSION = sys.version_info.major


class ItsLogger:
    MAX_RECORDS_PER_PROCESS = 1000
    MAX_RECORDS_PER_MESSAGE = 100

    def __init__(self, app='itslogger', write_to_redis=False, record_model=None):
        """

        :param app:
        :param write_to_redis: пока не используется
        :param record_model:
        """

        self.write_to_redis = write_to_redis
        self.record_model = record_model
        self.app = app or 'itslogger'

        self.types_dict = {}
        self.apps_dict = {}
        self.scripts_dict = {}

    def _write_log(self, log_type, message=None, app=None, exc_info=False, params=None, tag=None, add_rst=None,
                   level=log_levels.INFO, script_path='', lineno=0, trace_info=None, save=True, log_to_cron=False):

        """
        Создать запись лога

        :param log_type: строка - тип лога
        :param message: текст сообщения
        :param app: строка - имя приложения
        :param exc_info: Выводить traceback
        :param level: уровень
        :param script_path: путь к скрипту, вызвавшему метод
        :param lineno: номер строки
        :param trace_info: traceback
        :param params: дополнительные параметры
        :param save: сохранить запись
        :param tag: метка для фильтрации
        :param add_rst: добавить request_start_time к тегу из тредлокала
        :param log_to_cron: добавить запись в результат выполнения крон функции

        """

        from its_utils.app_logger.models import LogType, LoggedApp, LoggedScript

        if not message:
            # Гдето мы исползовали старый logging и там запись была (type=>message)
            # значит все придет в log_type и мы его разобеъем
            _ = log_type.split('=>')
            if len(_) > 1:
                log_type = _[0][:255]
                message = _[1]
            else:
                log_type = ""
                message = _[0]

        if log_to_cron:
            append_cron_result("{} {}=>{}".format(timezone.now(), log_type, message))


        if settings.DEBUG and level >= getattr(settings, 'ITS_LOGGER_CONSOLE_LEVEL', 0):
            try:
                # бывает что на какой-то системе выдает ошибку (linux)
                from logging import getLevelName
                print("{}: {} => {}".format(getLevelName(level), log_type, message))
            except:
                pass

        if app is None:
            app = self.app

        if self.write_to_redis:
            raise NotImplemented
            # TODO: записать параметры в редис, вызвать метод из крона c этими параметрами
            # params = dict(
            #     log_type=log_type, message=message, app=app,
            #     exception=exception, params=params, level=level,
            #     script_path=script_path, lineno=lineno, save=save
            # )
            #
            # return None

        # Получаем тип лога
        log_type_obj = self.__get_cached_object(LogType, self.types_dict, log_type)
        if log_type_obj and log_type_obj.level_save_to_db > level:
            return None

        # Получаем скрипт
        script_obj = self.__get_cached_object(LoggedScript, self.scripts_dict, script_path, field='pathname')
        if script_obj and script_obj.level_save_to_db > level:
            return None

        # Получаем приложение
        app_obj = self.__get_cached_object(LoggedApp, self.apps_dict, app)
        if app_obj and app_obj.level_save_to_db > level:
            return None

        if exc_info:
            info = sys.exc_info()
            if info[1]:
                # Если ошибка есть, то можно красиво показать ... но тут
                # Был вариант 1
                # exception_info = traceback.format_exc()

                # Вариант 2, но ловит последний попавшийся эксепшн, а не место вызова
                # from django.views.debug import ExceptionReporter
                # exception_info = ExceptionReporter(None, *info).get_traceback_html()

                # Вариант 3, пробуем его
                exception_info = trace_info

            else:
                exception_info = trace_info

        else:
            exception_info = ''

        if add_rst:
            tag = "{}-{}".format(tag, get_request_start_time())

        record = self.make_log_record(level=level,
                                      type=log_type_obj,
                                      app=app_obj,
                                      script=script_obj,
                                      message=message,
                                      tag=tag,
                                      params=params,
                                      exception_info=exception_info,
                                      lineno=lineno)
        record.before_save()
        if save:
            try:
                # Бывает ошибка ValueError: A string literal cannot contain NUL (0x00) characters.
                record.save()
            except ValueError:
                pass

            chat_list = record.get_telegram_chat_list()
            telegram_chat_async = app_settings.get_setting('ITS_LOGGER_TELEGRAM_ASYNC')
            for telegram_chat in chat_list:
                if telegram_chat_async:
                    post_to_telegram_async(telegram_chat, record.pretty_telegram_message)
                else:
                    post_to_telegram(telegram_chat, record.pretty_telegram_message)

            # # Отправить в телеграм
            # telegram_chat = getattr(settings, 'ITS_LOGGER_TELEGRAM_CHAT', -362379873)
            # telegram_chat_async = getattr(settings, 'ITS_LOGGER_TELEGRAM_ASYNC', True)
            # if telegram_chat and all(level >= obj.level_send_telegram for obj in (app_obj, log_type_obj, script_obj)):
            #     if telegram_chat_async:
            #         post_to_telegram_async(telegram_chat, record.pretty_telegram_message)
            #     else:
            #         post_to_telegram(telegram_chat, record.pretty_telegram_message)

        return record

    def make_log_record(self, **kwargs):
        from its_utils.app_logger.models import LogRecord
        log_record_model = self.record_model or LogRecord
        return log_record_model(**kwargs)



    def process_redis_queue(self):
        # НЕ ИСПЛЬЗУЕТСЯ!
        # берём настройки логирования скриптов
        from its_utils.app_logger.models import LogType, LoggedApp, LoggedScript, LogRecord
        self.scripts_dict = {script.pathname: script for script in LoggedScript.objects.all()}
        self.types_dict = {log_type.name: log_type for log_type in LogType.objects.all()}
        self.apps_dict = {log_type.name: log_type for log_type in LoggedApp.objects.all()}

        # TODO: получить список логов из редис
        redis_queue = []

        to_create = []
        count = 0
        for log_params in redis_queue:
            # save=False, так как сохраняем через bulk_create
            record = self._write_log(save=False, **log_params)
            if record:
                to_create.append(record)
                count += 1

        log_record_model = self.record_model or LogRecord
        log_record_model.objects.bulk_create(to_create)

        return count

    @staticmethod
    def __get_cached_object(obj_cls, cached_dict, name, field='name'):
        """
        Получить объект из словаря или базы данных
        """

        obj = None
        if name is not None:
            if cached_dict and False: ###!!!!!!!!!! Убрал действие кеша!! наверно постгрес сам должен кешировать частые запросы
                obj = cached_dict.get(name)

            if not obj:
                with transaction.atomic():
                    obj, _ = obj_cls.objects.get_or_create(**{field: name})
                if cached_dict is not None:
                    cached_dict[name] = obj

        return obj

    @staticmethod
    def __real_locals(drop_last_n_frames=1):
        """Возвращает locals в месте текущей ошибки (если есть) или
        до запрошенного фрейма.
        """
        _, __, tb = sys.exc_info() #Срабатывает ТОЛЬКО ПРИ обработке ошибок
        if tb:
            def collect_locals(level: int, tb: traceback) -> str:
                locals_string = """
locals level={}
    {}
                """.format(level,
                           pprint.pformat(tb.tb_frame.f_locals, 2, 100, depth=2))
                if tb.tb_next:
                    locals_string += collect_locals(level + 1, tb.tb_next)
                return locals_string


            return collect_locals(0, tb)
            # if tb.tb_next:
            #     frame = tb.tb_next.tb_frame
            # else:
            #     frame = tb.tb_frame
        else:
            stack_frame = inspect.stack()[drop_last_n_frames]
            frame = stack_frame.frame if PYTHON_VERSION > 2 else stack_frame[0]
            locals_ = frame.f_locals
            return 'ПРОВЕРЬТЕ в функции __real_locals!!!! \nlocals:\n%s' % pprint.pformat(locals_, 2, 100, depth=2)

    @staticmethod
    def __real_tb(drop_last_n_frames=1):
        """Возвращает ТБ до текущей ошибки (если есть) или до текущего фрейма.
        """
        if all(sys.exc_info()):
            # Есть ошибка, путь до нее
            return traceback.format_exc()
        # Нет ошибки, путь до текущего фрейма
        tb_lines = traceback.format_stack()
        if drop_last_n_frames:
            tb_lines = tb_lines[:-abs(drop_last_n_frames)]
        return 'Traceback (most recent call last):\n' + '\n'.join(tb_lines)

    def __call_write_log(self, level, exc_info, *args, request=None, **kwargs):
        """
        Получить информцию о скрипте, вызвавшем метод и записать скрипт
        """
        try:
            caller_stack_line = inspect.stack()[2]  # предпредпоследняя запись в стеке

            if PYTHON_VERSION > 2:
                script_path = caller_stack_line.filename  # путь к файлу
                lineno = caller_stack_line.lineno  # номер строки

            else:
                script_path = caller_stack_line[1]  # путь к файлу
                lineno = caller_stack_line[2]  # номер строки
        except:
            script_path = 'unknown script'
            lineno = 0  # номер строки


        trace_info = ''
        if exc_info:
            type, value, traceback = sys.exc_info()  # Срабатывает ТОЛЬКО ПРИ обработке ошибок
            if traceback:
                # В случае если поймали ошибку, то все хорошо и нам соберется HTML как при DEBUG True
                trace_info = LocalExceptionReporter(request, *sys.exc_info()).get_traceback_html()
            else:
                # Пропуск трех фреймов:
                #   - ItsLogger.{__real_tb|__real_locals}
                #   - ItsLogger.__call_write_log
                #   - ItsLogger.{info|debug|...}
                drop_n_frames = 3
                trace_info = "{exc}\n{locals}".format(
                     exc=self.__real_tb(drop_n_frames),
                     locals=self.__real_locals(drop_n_frames),
                )

        return self._write_log(
            *args,
            level=level, script_path=script_path, lineno=lineno, trace_info=trace_info, exc_info=exc_info,
            **kwargs
        )

    def info(self, log_type, message=None, app=None, exc_info=False, params=None, tag=None, add_rst=False, log_to_cron=False):
        """
        Записать лог уровня INFO

        :param log_type: строка - тип лога
        :param message: текст сообщения
        :param app: строка - имя приложения (необязательный)
        :param exc_info: выводить traceback в сообщении (необязательный)
        :param params: дополнительные параметры (необязательный)
        :param tag: Метка для фильтрации в админке (необязательный)
        """

        return self.__call_write_log(
            log_levels.INFO, log_type=log_type, message=message, app=app, exc_info=exc_info, params=params, tag=tag, add_rst=add_rst, log_to_cron=log_to_cron
        )

    def debug(self, log_type, message=None, app=None, exc_info=False, params=None, tag=None, add_rst=False, log_to_cron=False):
        """
        Записать лог уровня DEBUG

        :param log_type: строка - тип лога
        :param message: текст сообщения
        :param app: строка - имя приложения (необязательный)
        :param exc_info: выводить traceback в сообщении (необязательный)
        :param params: дополнительные параметры (необязательный)
        :param tag: Метка для фильтрации в админке (необязательный)
        """

        return self.__call_write_log(
            level=log_levels.DEBUG, log_type=log_type, message=message, app=app, exc_info=exc_info, params=params, tag=tag, add_rst=add_rst, log_to_cron=log_to_cron
        )

    def warning(self, log_type, message=None, app=None, exc_info=True, params=None, tag=None, add_rst=False, log_to_cron=False):
        """
        Записать лог уровня WARNING

        :param log_type: строка - тип лога
        :param message: текст сообщения
        :param app: строка - имя приложения (необязательный)
        :param exc_info: выводить traceback в сообщении (необязательный)
        :param params: дополнительные параметры (необязательный)
        :param tag: Метка для фильтрации в админке (необязательный)
        """

        return self.__call_write_log(
            level=log_levels.WARNING, log_type=log_type, message=message, app=app, exc_info=exc_info, params=params, tag=tag, add_rst=add_rst, log_to_cron=log_to_cron
        )

    warn = warning

    def error(self, log_type, message=None, app=None, exc_info=True, params=None, tag=None, add_rst=False, log_to_cron=False):
        """
        Записать лог уровня ERROR

        :param log_type: строка - тип лога
        :param message: текст сообщения
        :param app: строка - имя приложения (необязательный)
        :param exc_info: выводить traceback в сообщении (необязательный)
        :param params: дополнительные параметры (необязательный)
        :param tag: Метка для фильтрации в админке (необязательный)
        """

        return self.__call_write_log(
            log_levels.ERROR, log_type=log_type, message=message, app=app, exc_info=exc_info,
            params=params, tag=tag, add_rst=add_rst, log_to_cron=log_to_cron
        )

    exception = error

    def critical(self, log_type, message=None, app=None, exc_info=True, params=None, tag=None, add_rst=False, log_to_cron=False):
        """
        Записать лог уровня CRITICAL

        :param log_type: строка - тип лога
        :param message: текст сообщения
        :param app: строка - имя приложения (необязательный)
        :param exc_info: выводить traceback в сообщении (необязательный)
        :param params: дополнительные параметры (необязательный)
        :param tag: Метка для фильтрации в админке (необязательный)
        """

        return self.__call_write_log(
            log_levels.CRITICAL, log_type=log_type, message=message, app=app, exc_info=exc_info, params=params, tag=tag, add_rst=add_rst, log_to_cron=log_to_cron
        )

    def log(self, log_level, log_type, message=None, app=None,
            exc_info=None, params=None, tag=None, request=None):
        """Записать лог с log_level уровнем.
        """
        if exc_info is None:
            exc_info = log_level >= log_levels.WARNING
        return self.__call_write_log(
            log_level, log_type=log_type, message=message,
            app=app, exc_info=exc_info, params=params, tag=tag,
            request=request,
        )

    def process_logs(self, last_processed_log_id):
        """
        Отправить логи на почту

        :param last_processed_log_id: id последнего обработанного лога
        :return: новый id последнего обработанного лога или None
        """
        try:
            last_processed_log_id = self.record_model.objects.last().id
        except AttributeError:
            return last_processed_log_id, {}
        records_qs = self.record_model.objects.filter(
            id__gt=last_processed_log_id,
            level__gte=F('script__level_send_email')
        ).filter(
            level__gte=F('type__level_send_email')
        ).filter(
            level__gte=F('app__level_send_email')
        ).order_by('id')[:self.MAX_RECORDS_PER_PROCESS]  # Обрабатываем до 1000 записей за один вызов

        if not records_qs.exists():
            return last_processed_log_id, "sent 0"

        total_levels_counts = {}
        for records_chunk in make_chunks(list(records_qs), self.MAX_RECORDS_PER_MESSAGE):
            # Отправляем сообщения (до 100 запесей в каждом)

            messages = []
            levels_counts = {}  # сюда считаем количество логов разных типов {'INFO': 10, 'DEBUG': 2}
            most_critical = -1, ''  # самый критический лог - кортеж (level, display)

            for record in records_chunk:
                level_display = record.get_level_display()
                levels_counts[level_display] = levels_counts.get(level_display, 0) + 1
                total_levels_counts[level_display] = total_levels_counts.get(level_display, 0) + 1

                messages.append(record.pretty_message)

                if record.level > most_critical[0]:
                    most_critical = record.level, level_display


            subject = u'[{}] most_critical {}'.format(self.record_model._meta.app_label, most_critical[1])

            message = u'http://{}/admin/{}/{}/\n\n{}\n\n{}'.format(
                settings.DOMAIN, self.record_model._meta.app_label, self.record_model._meta.model_name,
                '\n'.join([u'{}: {}'.format(k, v) for k, v in levels_counts.items()]),
                '\n\n'.join(messages)
            )

            mail_admins(subject, message, fail_silently=True)

        return last_processed_log_id, total_levels_counts
