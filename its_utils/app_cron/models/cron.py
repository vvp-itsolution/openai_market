# -*- coding: UTF-8 -*-
import importlib
import inspect
import json
import os
import re
import sys
import traceback
import pytz

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

from its_utils.app_admin.get_admin_url import get_admin_url, get_admin_a_tag
from its_utils.app_telegram_post.post_to_telegram import post_to_telegram, post_to_telegram_async
from its_utils.functions import sys_call
from settings import ilogger
from its_utils.app_cron.cron_thread_local import cron_thread_local

class Cron(models.Model):
    name = models.CharField(max_length=255, help_text=u'Название крона для удобства')

    string = models.CharField(max_length=255, null=True, blank=True, help_text=u'Крон строка')
    repeat_seconds = models.IntegerField(null=True, blank=True,
                                         help_text=u'Через какое количество секунд запускать задачу.'
                                                   u'Если поле определено, то крон строка игнорируется')

    path = models.CharField(max_length=255,
                            help_text=u'Полный путь до функции. Синтаксис как питоновский импорт.'
                                      u'Например autotasks.t18816_add_row_for_ticket_with_tables.process_autotask')
    parameters = models.TextField(null=True, blank=True, help_text=u'JSON-параметры. Отправляются в функцию.')

    description = models.TextField(blank=True, default='', help_text=u'Описание')

    timeout = models.FloatField(null=False, blank=True, default=60, help_text=u'Время, через которое ожидается выполнение задачи.')
    active = models.BooleanField(blank=True, default=True, help_text=u'Активен крон или нет')
    started_time = models.DateTimeField(null=True, blank=True)
    concurrency = models.IntegerField(blank=True, default=1)
    process_filter = models.PositiveSmallIntegerField(help_text=u'В каком процессе запускать', default=1)

    class Meta:
        app_label = 'app_cron'

    def notificate(self, message):
        post_to_telegram_async(-397893466, message)

    def notificate_once(self, message):
        # Уведомить только в пределах одного созданного объекта
        # (раз в минуту на процесс максимум в стандартном варианте использования).
        if hasattr(self, 'notificated'):
            return
        self.notificate(message)
        ilogger.warning('cron_timeout', message)
        self.notificated = True

    def is_ready_to_start(self):
        # порверяем можно ли запустить крон

        if self.concurrency > 1:
            from its_utils.app_cron.models.cron_result import CronResult
            return CronResult.objects.filter(cron=self, finished=False).count() < self.concurrency


        started_time = Cron.objects.filter(pk=self.id).only('started_time')[0].started_time

        if started_time is None:
            return True

        if (timezone.now() - started_time).total_seconds() > self.timeout:
            # Если не вписались в разрешенный таймаут, то проверяем есть ли процесс на ту минуту
            is_process_exists = self.cron_process_exists()
            if not is_process_exists:
                # Какая то бага произошла и скрипт повалился надо разрешить дальше выполнять
                message = (
                    'Крон разлочен т.к не был найден запускающий процесс  экземпляр не запущен {}'.format(
                        get_admin_a_tag(self)))

                self.notificate_once(message)
                Cron.objects.filter(started_time=started_time, id=self.id).update(started_time=None)
                return True

            from its_utils.app_cron.models import CronResult
            message = (
                'Новый экземпляр не запущен <a href="{url}">{name}</a>, '
                'т.к. предыдущий ({instance}) не завершен за {sec} сек. timeout={timeout}, '
                'крон на ту минуту {process_exists}СУЩЕСТВУЕТ'.format(
                    url=get_admin_url(self),
                    name=self.name,
                    instance=get_admin_a_tag(CronResult.objects.filter(cron=self).last(), "запущеный экземпляр"),
                    sec=str((timezone.now() - started_time).total_seconds()).split('.')[0],
                    timeout=self.timeout,
                    process_exists='' if is_process_exists else 'НЕ '
                )
            )

            self.notificate_once(message)
            #post_to_telegram_async(-397893466, message)
            #ilogger.warning('cron_timeout', message)

    def grep_cron_process(self, started_time=None):
        if not self.started_time:
            return None

        path = '[/]'.join(os.path.abspath(os.path.dirname(__file__)).split('/models'))
        print(path)
        command = 'ps -aux | grep "{path}.*{process_filter}{start_time}"'.format(
            path=path,
            process_filter=self.process_filter,
            start_time=(
                ' {0:%Y%m%d-%H:%M}'.format(started_time.astimezone(tz=pytz.timezone('Europe/Moscow')))
                if started_time else ''
            ),
        )
        print(command)
        return_code, output = sys_call(command)
        print(return_code, output)

        return output.decode()

    def get_cron_process_id(self):
        output = self.grep_cron_process(started_time=self.started_time)

        if not output:
            return None

        # id процесса - второе значение в выводе
        # kdb 18968 92.0 0.8 905616 72228 ? Sl 21:36 0:01 path/to/python path/to/cron.py 1 20211201-21:36:01
        try:
            return re.split(' +', output)[1]
        except:
            return -1

    def kill_cron(self):
        if not self.started_time:
            return 'крон не запущен'

        if (timezone.now() - self.started_time).total_seconds() <= self.timeout:
            return 'процесс запущен меньше {} с. назад'.format(self.timeout)

        process_id = self.get_cron_process_id()
        if not process_id:
            return 'процесс не найден'

        if process_id == -1:
            return 'не удалось получить id процесса'

        sys_call('kill {}'.format(process_id))
        return 'завершён процесс {}'.format(process_id)

    def cron_process_exists(self):
        """
        Провертиь, существеут ли процесс, в котором выполняется крон-функция

        https://ts.it-solution.ru/#/ticket/60114/
        """

        return self.get_cron_process_id() is not None

        # status = os.popen('ps -fu $USER | grep "cron.py {process_filter} {started_time:%Y%m%d-%H:%M}"'.format(
        #     process_filter=self.process_filter,
        #     started_time=self.started_time.astimezone(tz=pytz.timezone('Europe/Moscow'))
        # )).read()
        # 'app_cron' in status
        #
        # # Кроме крон-процесса в результат grep могут попасть две строки - команды, которые мы вызываем:
        # #
        # # vkleads   5653  4213  0 19:11 pts/7    00:00:00 sh -c ps -fu vkleads | grep "cron.py 2 20191017-19:11"
        # # vkleads   5655  5653  0 19:11 pts/7    00:00:00 grep cron.py 2 20191017-19:11
        # #
        # # Поэтому проверяем вхождение подстроки "app_cron" (кусочек пути к файлу cron.py), который должна содержать
        # # строка, соответствующая процессу, который мы ищем, но которой не должно быть в двух строках выше
        # return 'app_cron' in status

    def eval_cron(self, cron_log_id=0):

        log_prefix = "cron_id:{}".format(self.pk)

        # if cron_log_id:
        #     try:
        #         import prctl
        #         prctl.set_name("{} {}".format(self.path, cron_log_id))
        #     except:
        #         pass

        start = timezone.now()
        if self.concurrency == 1 and Cron.objects.filter(pk=self.id, started_time=None).update(started_time=start) == 0:
            #Другой тред? успел схватить выполнение этого крона
            return

        from its_utils.app_cron.models import CronResult
        #было так cron_result = CronResult(cron=self, start=start, cron_started=CRON_STARTED, cron_log_id=cron_log_id)
        cron_result = CronResult(cron=self, start=start, cron_started=start, cron_log_id=cron_log_id)
        cron_result.save()
        cron_thread_local.cron_result = cron_result
        self.started_time = start
        self.save(force_update=True, update_fields=['started_time'])
        last_dot_index = self.path.rfind('.')
        module, function = self.path[:last_dot_index], self.path[last_dot_index + 1:]
        result = None

        print('{} Trying to run {}: {}'.format(log_prefix, self, self.path))
        ilogger.debug('cron_log', '{} Trying to run {}: {}'.format(log_prefix, self, self.path))
        try:
            try:
                module = importlib.import_module(module)

            except ImportError:
                # взоможно, прописан путь к класс-методу
                class_path, class_name = module.rsplit('.', maxsplit=1)
                module = importlib.import_module(class_path)
                module = getattr(module, class_name)

        except Exception:
            print("{} {}".format(log_prefix, traceback.format_exc()), file=sys.stderr)
            ilogger.error('cron_log', "Exception {}".format(get_admin_a_tag(self)))
            result = 'ошибка'

        else:
            function = getattr(module, function, None)

            if not (function and callable(function)):
                print("{} {}".format(log_prefix, traceback.format_exc()), file=sys.stderr)
                ilogger.error('cron_log', "not (function and callable(function))")
                result = 'ошибка'
            else:
                try:
                    if self.parameters:
                        parameters = json.loads(self.parameters)
                    else:
                        parameters = {}

                    if 'cron_params' in inspect.signature(function).parameters:
                        parameters['cron_params'] = {"start_time": start}

                    ilogger.debug('cron_log', '{} Запускаем'.format(log_prefix))
                    result = function(**parameters)
                    ilogger.debug('cron_log', '{} Завершилось выполнение'.format(log_prefix))

                    print("{} результат {}".format(log_prefix, result))


                except Exception:

                    print("{} {}".format(log_prefix, traceback.format_exc()), file=sys.stderr)
                    ilogger.exception('cron_error', '{} ошибочка в <a href="{}">{}</a>'.format(log_prefix, get_admin_url(self), self.name))
                    result = traceback.format_exc()

        #Пробуем снять флаг прочтения, но только если мы его сами ставили, для предотваращения наложений.
        #Получается что снять может только последний запущенный процесс
        if self.concurrency == 1:
            res = Cron.objects.filter(started_time=start, id=self.id).update(started_time=None)
            print("{} снимаем лок крона {}удачно".format(log_prefix, '' if res else 'не '))
            ilogger.debug('cron_log', "{} снимаем лок крона {}удачно".format(log_prefix, '' if res else 'не '))

        cron_result.append_text(result)
        CronResult.objects.filter(pk=cron_result.pk).update(
            end=timezone.now(),
            finished=True,
        )
        cron_time = cron_result.time()
        cron_thread_local.cron_result = None
        if self.timeout is not None and cron_time and cron_time.total_seconds() > self.timeout:
            message = 'превышено время выполнения {} сек крона <a href="{}">{}</a> с <a href="{}">результатом</a>'\
                .format(cron_time, get_admin_url(self), self.name, get_admin_url(cron_result))
            post_to_telegram_async(-397893466, message)
            ilogger.warning('cron_timeout', message)

            # send_message_in_ticket(
            #     U'Задача "%s" выполнялась дольше запланированного времени: %s\n' % (self.name, cron_time))
            pass

    def check_unfinished_tasks(self):
        if not self.timeout:
            return

        from its_utils.app_cron.models import CronResult

        timeout_ago = timezone.now() - timezone.timedelta(seconds=self.timeout)
        expired_cron_results = CronResult.objects.filter(
            cron=self, finished=False, end__isnull=True, start__lt=timeout_ago
        ).only(
            'id', 'cron_id', 'start'
        )

        if expired_cron_results.exists():
            self.notificate('Возможная блокировка запуска {} т.к выполняется дольше таймаута,'.format(
                get_admin_a_tag(self)
            ))

    def clean(self):

        if not (self.string or self.repeat_seconds):
            raise ValidationError('You must provide either string or repeat_seconds value')

        if self.repeat_seconds is not None and not 1 <= self.repeat_seconds <= 60:
            raise ValidationError({'repeat_seconds': 'Must be between 1 and 60'})

        if not self.check_if_string_is_correct(self.string):
            raise ValidationError({'string': 'Cron string is not correct'})

        try:
            if self.parameters:
                json.loads(self.parameters)
        except ValueError:
            raise ValidationError({'parameters': 'Bad json'})

    @staticmethod
    def check_if_string_is_correct(string):
        return True

    def __unicode__(self):
        return self.name

    if sys.version_info.major > 2:
        __str__ = __unicode__
