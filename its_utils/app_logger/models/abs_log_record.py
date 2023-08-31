# coding: utf-8
from logging import ERROR

try:
    from django.db.models import JSONField
except:
    from django.contrib.postgres.fields import JSONField

from django.db import models
from django.template import Template, Context
from django.utils import timezone

from its_utils.app_admin.get_admin_url import get_admin_url, get_admin_list_url
from its_utils.app_logger import app_settings
from its_utils.functions import datetime_to_string
from its_utils.app_logger.utils import log_levels
from django.conf import settings


class AbsLogRecord(models.Model):
    """
    Описывает сообщение в логе
    """

    level = models.SmallIntegerField(choices=log_levels.LOG_LEVEL_CHOICES, default=log_levels.INFO,
                                     verbose_name=u'Уровень')

    type = models.ForeignKey('app_logger.LogType', on_delete=models.CASCADE, verbose_name=u'Тип')
    app = models.ForeignKey('app_logger.LoggedApp', on_delete=models.CASCADE,
                            verbose_name=u'Приложение')

    date_time = models.DateTimeField(default=timezone.now, verbose_name=u'Время')

    date = models.DateField(default=timezone.now, verbose_name=u'Дата', null=True)

    message = models.TextField(default='', verbose_name=u'Сообщение')
    exception_info = models.TextField(default='', verbose_name=u'Исключение')

    script = models.ForeignKey('app_logger.LoggedScript', on_delete=models.CASCADE, verbose_name=u'Скрипт')
    lineno = models.IntegerField(null=True, verbose_name=u'Номер строки')

    tag = models.CharField(verbose_name=u'Метка для фильтрации', default="", null=True, blank=True, db_index=True, max_length=50)

    params = JSONField(null=True, blank=True, verbose_name=u'Параметры')

    from its_utils.django_postgres_fuzzycount.fuzzycount import FuzzyCountManager
    objects = FuzzyCountManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        return (u'[{type}][{level}]({path})({lineno})({date_time})\n'
                u'{message}\n{admin_url}'.format(type=self.type,
                                                 level=self.get_level_display(),
                                                 path=self.script,
                                                 lineno=self.lineno,
                                                 date_time=datetime_to_string(self.date_time),
                                                 message=self.message,
                                                 admin_url=get_admin_url(self)))

    __str__ = __unicode__

    @property
    def pretty_message(self):
        return u'[{}][{}]({})({})({})\n{}\n{}'.format(
            self.type, self.get_level_display(), self.script, self.lineno, datetime_to_string(self.date_time),
            self.message, get_admin_url(self)
        )

    @property
    def pretty_telegram_message(self):
        return (
            u'[{type}][{level}] {usertag}\n'
            u'{message}\n'
            u'<a href="{admin_url}">подробнее</a> {tag_part}'.format(
                type=self.type,
                level=self.get_level_display(),
                usertag=(
                    app_settings.get_setting('ITS_LOGGER_TELEGRAM_ERROR_TAG')
                    if self.level >= ERROR
                    else ""
                ),
                message=self.message,
                admin_url=get_admin_url(self),
                tag_part=(
                    'по тегу <a href="{url}?tag={tag}">{tag}</a>'.format(
                        url=get_admin_list_url(self),
                        tag=self.tag,
                    )
                    if self.tag
                    else ""
                )
            )
        )

    @property
    def pretty_telegram_message_escaped(self):
        """Джанго-шаблон нужен для экранирования html, иначе при отправке
        сообщения с разметкой возникает такая ошибка:
            tickets_bot, [19.12.19 13:59]
            Не отправилось 500 b'Error! Can\'t parse entities: unsupported start tag "html" at byte offset 26'

            tickets_bot, [19.12.19 13:59]
            [bitrix_api_error][ERROR]
            <html>
            <head><title>403 Forbidden</title></head>
            <body bgcolor="white">
            <center><h1>403 Forbidden</h1></center>
            <hr><center>nginx/1.10.2</center>
            </body>
            </html>

            <a href="https://articles.it-solution.ru/admin/app_logger/logrecord/24379097/change/">подробнее</a>
        """
        t = '[{{ self.type }}][{{ self.get_level_display }}]\n' \
            '{{ self.message }}\n' \
            '<a href="{{ admin_url }}">подробнее</a>'
        return Template(t).render(Context(dict(
            self=self,
            admin_url=get_admin_url(self),
        )))

    def before_save(self):
        """
        Метод вызывается перед сохранением записи ItsLogger'ом
        """

        raise NotImplemented

    def get_telegram_chat_list(self):
        # вернет список чатов, в которые будет писать
        chat_list = []

        # если этот тип логов отложен меньше чем на 35 дней то не оптавляем
        if self.type.postpone and (self.type.postpone - timezone.now().date()).days in range(0, 35):
            return []

        # писать куда-либо будет только если все уровни удовлетворяют
        if all(self.level >= obj.level_send_telegram for obj in (self.app, self.type, self.script)):

            default_chat_id = '-362379873'
            chat_id_from_settings = app_settings.get_setting('ITS_LOGGER_TELEGRAM_CHAT')
            chat_id_from_app = self.app.telegram_chat
            chat_id_from_type = self.type.telegram_chat

            if chat_id_from_type:
                chat_list.append(chat_id_from_type)  # типовой в любом случае если есть

            if chat_id_from_app:
                chat_list.append(chat_id_from_app)
            elif chat_id_from_settings:
                chat_list.append(chat_id_from_settings)  # чат приложения, если его нет то чат из настроек

            if not chat_list:
                chat_list.append(default_chat_id)  # если нет ни 1 чата - то хотя бы дефолтный

        return chat_list
