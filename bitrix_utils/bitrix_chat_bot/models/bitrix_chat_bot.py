# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import base64
import json
import os

from django.conf import settings
from django.db import models
from django.db.models.deletion import PROTECT
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import six

from bitrix_utils.bitrix_auth.functions.bitrix_user_required import bitrix_user_required
from bitrix_utils.bitrix_auth.models import BitrixUserToken, BitrixUser
from bitrix_utils.bitrix_chat_bot.exceptions import EventVerificationError
from bitrix_utils.bitrix_auth.models.bitrix_user_token import BitrixApiError
from settings import ilogger

if not six.PY2:
    from typing import Union

"""
https://dev.1c-bitrix.ru/learning/course/?COURSE_ID=93
"""


@six.python_2_unicode_compatible
class BitrixChatBot(models.Model):
    # Можно попробовать брать из application.redirect_url
    EVENT_URL = "/chat_bot_event/"
    DOMAIN = None
    CODE = ""
    DEFAULT_MESSAGE = 'На связи... default_message..'
    TYPE = "B"
    OPENLINE = "Y"
    CLIENT_ID = None
    GENDER = "M"
    NAME = "Типовой бот"
    SHORT_DESCRIPTION = "Типовое описание"
    AVATAR = 'bitrix_utils/bitrix_chat_bot/assets/logo.png'

    APP = None
    EVENT_LOG_MODEL = None

    application = models.ForeignKey('bitrix_auth.BitrixApp', related_name='+', on_delete=PROTECT)
    author = models.ForeignKey('bitrix_auth.BitrixUser', on_delete=PROTECT)

    is_active = models.BooleanField(default=False)
    bitrix_id = models.CharField(max_length=100, default="", blank=True)

    class Meta:
        abstract = True
        unique_together = 'bitrix_id', 'author', 'application',

    def __str__(self):
        return u'%s @ %s' % (self.bitrix_id, self.author.portal.domain)

    def __init__(self, *args, request=None, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.event = event
        self._token_cache = {}

    @property
    def portal(self):
        return self.author.portal

    def get_token(self, user=None):
        if not user:
            user = self.author

        if user.id in self._token_cache:
            return self._token_cache[user.id]

        token = BitrixUserToken.objects.get(user=user, application=self.application)

        if not token.is_active:
            token = BitrixUserToken.get_random_token(
                application_name=self.application.name,
                portal_id=user.portal.id,
                is_admin=False
            )
            if token:
                self.author = token.user
                self.save()
                self._token_cache[token.user.id] = token
        else:
            self._token_cache[user.id] = token
        return token

    def get_registration_fields(self):
        """
        Возвращает словарь, который используется при регистрации и обновлении бота
        """

        with open(os.path.join(settings.BASE_DIR, self.AVATAR), "rb") as image_file:
            bot_face = base64.b64encode(image_file.read())

        event_url = "https://{}{}".format(
            self.DOMAIN or self.application.domain,
            self.EVENT_URL)

        # Параметры периодически меняются следим за документацией
        # https://dev.1c-bitrix.ru/learning/course/index.php?COURSE_ID=93&LESSON_ID=7873#imbot_register

        return {
            'CODE': self.CODE,
            'TYPE': self.TYPE,
            'EVENT_HANDLER': event_url,
            'OPENLINE': self.OPENLINE,
            'CLIENT_ID': self.CLIENT_ID,
            'PROPERTIES': {
                'NAME': self.NAME,
                'COLOR': 'MINT',
                'PERSONAL_BIRTHDAY': '2016-03-11',
                'WORK_POSITION': self.SHORT_DESCRIPTION,
                'PERSONAL_WWW': 'http://it-solution.ru',
                'PERSONAL_GENDER': self.GENDER,
                'PERSONAL_PHOTO': bot_face
            }
        }

    def register(self):
        """
        Регистрация бота
        """

        fields = self.get_registration_fields()
        bitrix_id = self.make_request('imbot.register', fields)

        if bitrix_id:
            self.bitrix_id = bitrix_id
            self.is_active = True
            self.save()

            return True
        else:
            return False

    def app_register(self, code, iframe, iframe_width=300, iframe_height=300, hash="d1ab17949a5747896523db0d5b349cd2"):
        """
            'BOT_ID' => 62, // идентификатор бота владельца приложения для чата
            'CODE' => 'echo', // код приложения для чата
            'IFRAME' => 'https://marta.bitrix.info/iframe/echo.php',
            'IFRAME_WIDTH' => '250', // рекомендованная ширина фрейма
            'IFRAME_HEIGHT' => '50', // рекомендованная высота фрейма
            'HASH' => 'd1ab17949a572b0979d8db0d5b349cd2', // токен для доступа к вашему фрейму для проверки подписи, 32 символа.
            'ICON_FILE' => '/* base64 image */', // Иконка вашего приложения - base64
            'CONTEXT' => 'BOT', // контекст приложения
                    ALL - приложение будет доступно во всех чатах
                    USER - приложение будет доступно только в чатах Один-на-один
                    CHAT - приложение будет доступно только в групповых чатах
                    BOT - приложение будет доступно только у бота, который установил приложение
                    LINES - приложение будет доступно только в чатах Открытых линий
                    CALL - приложение будет доступно только в чатах созданных в рамках Телефонии
            'HIDDEN' => 'N', // скрытое приложение или нет
            'EXTRANET_SUPPORT' => 'N', // доступна ли команда пользователям экстранет, по умолчанию N
            'LANG' => Array( // массив переводов, желательно указывать как минимум для RU и EN
            Array('LANGUAGE_ID' => 'en', 'TITLE' => 'Echobot IFRAME', 'DESCRIPTION' => 'Open Echobot IFRAME app', 'COPYRIGHT' => 'Bitrix24'),
        )
        :return:
        """

        pass

    def unregister(self, token=None):
        """
        Удалить бота с портала
        """
        unregistered = self.make_request('imbot.unregister', {
            'BOT_ID': self.bitrix_id
        }, token=token)
        if unregistered:
            self.is_active = False
            self.save()

    def update(self):
        """
        Обновление данных бота
        """

        fields = self.get_registration_fields()
        return self.make_request('imbot.update', {
            'BOT_ID': self.bitrix_id,
            'FIELDS': fields
        })

    def make_request(self, method, fields=None, token=None):
        """
        Запрос к API Bitrix24
        """

        if not token:
            token = self.get_token()

        response = token.call_api_method(api_method=method, params=fields, timeout=10)
        return response['result']

    def register_command(self, command_name, command_title=None, params='', common=False, hidden=False):
        """
        Регистрация команды
        https://dev.1c-bitrix.ru/learning/course/?COURSE_ID=93&LESSON_ID=7893&LESSON_PATH=7657.7871.7877.7893#imbot_command_register
        """

        return self.make_request('imbot.command.register', {
            'BOT_ID': self.bitrix_id,
            'COMMAND': command_name,
            'COMMON': 'Y' if common else 'N',
            'HIDDEN': 'Y' if hidden else 'N',
            'EVENT_COMMAND_ADD': 'https://{}{}'.format(
                self.DOMAIN or self.application.domain,
                self.EVENT_URL,
            ),
            'LANG': [{
                'LANGUAGE_ID': 'ru',
                'TITLE': command_title or command_name,
                'PARAMS': params
            }]
        })

    def unregister_command(self, command_id):
        """
        Удаление команды
        """

        return self.make_request('imbot.command.unregister', {
            'COMMAND_id': command_id,
        })

    def bind_event_handler(self, event, handler, bind_type='online'):
        response = self.make_request('event.bind', {
            'EVENT': event,
            'HANDLER': 'https://{}{}'.format(
                self.DOMAIN or self.application.domain,
                handler,
            ),
            'TYPE': bind_type,
        })
        return response

    def unbind_event_handler(self, event, handler):
        response = self.make_request('event.unbind', {
            'EVENT': event,
            'HANDLER': handler,
        })
        return response

    def send_message(
            self,
            chat_id,  # type: Union[int, str]
            text,  # type: str
            is_chat=False,  # type: bool
            keyboard=None,  # type: dict
            attach=None,  # type: dict
            url_preview=True,  # type: bool
            system=False,  # type: bool
    ):  # type: (...) -> int
        """Отправить сообщение от имени бота

        NB! параметр текст будет интерпретирован битриксом как BBCODE,
        для избежания нежелательного форматирования при выводе данных
        из внешних источников, которые могут поломать разметку
        можно использовать bitrix_utils.bb_code.escape.bb_template

        :param chat_id: id диалога, например self.event['dialog_id']
        :param text: текст сообщения BBCODE
        :param is_chat: преобразовать id диалога в 'chat' + id
        :param keyboard: кнопки действий
            https://dev.1c-bitrix.ru/learning/course/index.php?COURSE_ID=93&LESSON_ID=7683&LESSON_PATH=7657.7677.7683
        :param attach: вложения
            https://dev.1c-bitrix.ru/learning/course/index.php?COURSE_ID=93&LESSON_ID=7865
        :param url_preview: вкл/выкл генерации превьюшки URL под сообщением
        :param system: вкл/выкл отправку обезличенным серым системным сообщением
        :returns: id сообщения в чате
        """
        if not isinstance(is_chat, bool):
            raise RuntimeError('"is_chat" must be bool type')

        dialog_id = 'chat{}'.format(chat_id) if is_chat else chat_id

        fields = {
            'BOT_ID': self.bitrix_id,
            'DIALOG_ID': dialog_id,
            'MESSAGE': text,
            'URL_PREVIEW': 'Y' if url_preview else 'N',
            'SYSTEM': 'Y' if system else 'N',
        }

        if keyboard:
            fields['KEYBOARD'] = keyboard

        if attach:
            fields['ATTACH'] = attach

        return int(self.make_request('imbot.message.add', fields))

    def get_dialog_messages(self):
        """Возвращает предыдущие сообщения в данном чате, пример:

        >>> from pprint import pprint
        >>> pprint(self.get_dialog_messages()['result']['messages'])
        [{'author_id': 0,
          'chat_id': 109,
          'date': '2020-04-10T16:04:59+03:00',
          'id': 869,
          'params': None,
          'text': 'Обращение направлено на [USER=45]Бот Открытой Линии[/USER]',
          'unread': False}, ...]

        NB! В ответ не включается сообщение, которое инициировало запрос
        NB! Возвращает до 20 сообщений, не тестировал сработает ли с call_list
        """
        params = dict(DIALOG_ID=self.event['dialog_id'])
        if self.event['message_id']:
            params['LAST_ID'] = self.event['message_id']
        return self.get_token().call_api_method(
            'im.dialog.messages.get',
            params,
        )

    def is_first_message(self):
        """Смотрит первое ли это сообщение пользователя. Для этого росматривает
        нет ли сообщения пользователя в предыдущих 20 сообщениях.
        """
        messages = self.get_dialog_messages()['result']['messages']
        return all(int(message['author_id']) != int(self.event['author_id'])
                   for message in messages)

    def send_typing(self, dialog_id=None):
        """Послать, что бот печатает сообщение, похоже не работает в ОЛ %(
        :param dialog_id: self.event['dialog_id']
        """
        if dialog_id is None:
            dialog_id = self.event['dialog_id']
        return self.make_request('imbot.chat.sendTyping', dict(
            BOT_ID=self.bitrix_id,
            DIALOG_ID=dialog_id,
        ))

    def leave_chat(self, chat_id=None):
        """Покинуть чат
        """
        if chat_id is None:
            chat_id = self.event['chat_id']
        return self.make_request('imbot.chat.leave', dict(
            BOT_ID=self.bitrix_id,
            CHAT_ID=chat_id,
        ))

    def get_dialog(self, dialog_id=None):
        """Получить описание диалога (хз чем отличается от чата)
        https://dev.1c-bitrix.ru/learning/course/index.php?COURSE_ID=93&LESSON_ID=12888&LESSON_PATH=7657.7871.8023.12888
        :returns:
            {
                "id": "21191",
                "title": "Мятный чат №3",
                "owner": "2",
                "extranet": false,
                "avatar": "",
                "color": "#4ba984",
                "type": "chat",
                "entity_type": "",
                "entity_data_1": "",
                "entity_data_2": "",
                "entity_data_3": "",
                "date_create": "2017-10-14T12:15:32+02:00",
                "message_type": "C",
            }
        """
        if dialog_id is None:
            dialog_id = self.event['dialog_id']

        return self.make_request('imbot.dialog.get', dict(DIALOG_ID=dialog_id))

    def send_default_message(self, chat_id):
        """
        Отправить сообщение по умолчанию
        """

        self.send_message(chat_id, self.DEFAULT_MESSAGE)

    @staticmethod
    def parse_bot_event(request):
        """
        Получить поля события из запроса
        """

        def find_by_postfix(source, postfix):
            found_id_field = list(filter(lambda key: key[-len(postfix):] == postfix, source.keys()))
            return source.get(found_id_field[0]) if len(found_id_field) else None

        def as_bool(source, key):
            return (source[key] == 'Y') if key in source else None

        return {
            'domain': request.POST.get('auth[domain]'),
            'type': request.POST.get('event'),
            'bot_id': find_by_postfix(request.POST, '[BOT_ID]'),

            # Пользователь переданного токена, битрикс передает
            # токен написавшего боту
            'user_id': request.POST.get('auth[user_id]'),
            'access_token': request.POST.get(u'auth[access_token]'),
            'refresh_token': request.POST.get(u'auth[refresh_token]'),
            'member_id': request.POST.get('auth[member_id]'),

            # ID диалога и чата, чем отличаются кроме префикса 'chat' не ясно
            'dialog_id': request.POST.get('data[PARAMS][DIALOG_ID]'),
            'chat_id': request.POST.get('data[PARAMS][CHAT_ID]'),
            # Сообщение, вызвавшее событие
            'message': find_by_postfix(request.POST, '[MESSAGE]'),
            'message_id': find_by_postfix(request.POST, '[MESSAGE_ID]'),
            # ID ответственного за чат, у открытой линии, которую не взяли '0'
            'owner_id': request.POST.get('data[PARAMS][CHAT_AUTHOR_ID]'),

            # Данные написавшего сообщение
            'author_id': request.POST.get('data[USER][ID]'),
            'author_is_bot': as_bool(request.POST, 'data[USER][IS_BOT]'),
            'author_is_connector': as_bool(request.POST, 'data[USER][IS_CONNECTOR]'),
            'author_is_network': as_bool(request.POST, 'data[USER][IS_NETWORK]'),
            'author_is_extranet': as_bool(request.POST, 'data[USER][IS_EXTRANET]'),
            'author_name': request.POST.get('data[USER][NAME]'),
            'author_last_name': request.POST.get('data[USER][LAST_NAME]'),

            # Похоже это для команд `/somebotaсtion`
            'command': find_by_postfix(request.POST, u'[COMMAND]'),
            'command_params': find_by_postfix(request.POST, u'[COMMAND_PARAMS]'),
            'command_context': find_by_postfix(request.POST, u'[COMMAND_CONTEXT]')
        }

    @classmethod
    @csrf_exempt
    def event_view(cls, request):
        """
        View для обработки событий
        https://dev.1c-bitrix.ru/learning/course/?COURSE_ID=93&LESSON_ID=7881&LESSON_PATH=7657.7871.7881#onimcommandadd
        """

        event = cls.parse_bot_event(request)
        # TODO возможно надо от этого отказаться, но пока название команды берем отсюда
        request.event = event

        bot = cls.objects.get(author__portal__member_id=event['member_id'],
                              bitrix_id=event['bot_id'])
        bot.request = request
        bot.event = event

        from its_utils.app_logger.its_logger import ItsLogger
        logger = ItsLogger(app=cls.APP, record_model=cls.EVENT_LOG_MODEL)

        params = dict()

        for key, value in request.POST.items():
            params[key] = value

        for key, value in request.GET.items():
            params[key] = value

        logger.info('bitrix_bot_event',
                    message='params: {}\nevent: {}'.format(
                        json.dumps(params, indent=4, ensure_ascii=False),
                        json.dumps(event, indent=4, ensure_ascii=False)
                    ),
                    params=dict(bot_id=bot.id))

        try:
            bot.verify_event()
        except EventVerificationError as e:
            logger.info(
                'bitrix_bot_event_verification_error',
                'e: {e!r}\nparams: {params!r}'.format(e=e, params=params),
            )
            return e.http_response()

        request.bx_portal = bot.portal
        request.bx_user_token = bot.get_event_token()
        request.bx_user = request.bx_user_token.user

        bot.on_event_received(request)

        return HttpResponse(status=200)

    def get_event_user(self):
        user, _ = BitrixUser.objects.get_or_create(
            portal=self.portal,
            bitrix_id=int(self.event['user_id']),
            defaults=dict(email=''),
        )

        try:
            user_data = self.get_token().call_api_method('user.get', {
                'ID': user.bitrix_id,
                'ADMIN_MODE': 'Y',
            })['result'][0]
        except (BitrixApiError, IndexError):
            return user

        user.update_from_bx_response(user_data)
        return user

    def get_event_token(self):
        now = timezone.now()

        user = self.get_event_user()
        token, _ = BitrixUserToken.objects.get_or_create(
            application=self.application,
            user=user,
            defaults=dict(auth_token_date=now),
        )

        token.auth_token = self.event['access_token']
        refresh_token = self.event.get('refresh_token')
        if refresh_token:
            token.refresh_token = refresh_token

        token.auth_token_date = now
        token.is_active = True
        token.refresh_error = 0
        token.save()

        return token

    def verify_event(self):
        """
        Проверка подлинности присланного события.
        :raises: EventVerificationError
        """

        # Получаем параметры авторизации
        auth = {}
        for key in ['member_id', 'access_token', 'application_token']:
            auth_key = 'auth[%s]' % key
            try:
                auth[key] = self.request.POST[auth_key]
            except KeyError:
                raise EventVerificationError('no {}'.format(key))

        # Проверяем верифицируется ли запрос
        if self.portal.verify_online_event(
                application_name=self.application.name,
                access_token=auth['access_token'],
                application_token=auth['application_token'],
        ):
            return

        # Запрос с нашей точки зрения поддельный, авторизация недостоверна
        raise EventVerificationError('invalid auth: {0!r}'.format(auth))

    def on_event_received(self, request):
        """
        Обработка события
        """

        if self.event['type'] == 'ONIMBOTMESSAGEADD':
            self.on_message_add(request)

        elif self.event['type'] == 'ONIMCOMMANDADD':
            try:
                getattr(self, "on_command_{}".format(self.event['command']))(request)
            except AttributeError:
                self.on_command_add(request)

        elif self.event['type'] == 'ONIMBOTJOINCHAT':
            self.on_join_chat(request)

        elif self.event['type'] == 'ONIMBOTDELETE':
            self.on_bot_delete(request)

        elif self.event['type'] == 'ONIMBOTMESSAGEUPDATE':
            self.on_message_update(request)

        elif self.event['type'] == 'ONIMBOTMESSAGEDELETE':
            self.on_message_delete(request)

        elif self.event['dialog_id']:
            #self.send_default_message(self.event['dialog_id'])
            self.send_message(self.event['dialog_id'], "Бот получил неизвестное событие {}".format(self.event['type']))
            ilogger.error('newbotevent', "Бот получил неизвестное событие {}".format(self.event['type']))

    def on_message_add(self, request):
        """
        Переопределить для обработки события добавления сообщения
        """

        self.send_default_message(self.event['dialog_id'])

    def on_join_chat(self, request):
        """
        Переопределить для обработки добавления бота в чат
        """

        self.send_default_message(self.event['dialog_id'])

    def on_command_add(self, request):
        """
        Переопределить для обработки команд.
        """

        self.send_default_message(self.event['dialog_id'])

    def on_message_delete(self, request):
        """
        Переопределить для обработки удаления сообщений.
        """

        pass

    def on_bot_delete(self, request):
        """
        Переопределить для обработки события удаления бота
        """

        if self.is_active:
            self.is_active = False
            self.save()

    def on_message_update(self, request):
        """
        Переопределить для обработки события изменения сообщения в чате
        NB! Битрикс присылает в поле DIALOG_ID просто 'chat', для уточнения использовать CHAT_ID
        """

        pass

    @staticmethod
    @bitrix_user_required
    def __get_bx_user_from_request(request):
        """
        Применить bitrix_user_required
        """

        return request.bx_user

    @classmethod
    def register_view(cls, request):
        """
        View для регистрации бота. Всегда переопределяется. Проще всего вызовом метода register_or_update_bot_from_view,
        передав обязательные параметры
        """

        raise NotImplementedError()

    @classmethod
    def unregister_view(cls, request):
        """
        View для удаления бота.
        """

        bx_user = cls.__get_bx_user_from_request(request)

        try:
            bot = cls.objects.get(author__portal__domain=bx_user.portal.domain)

        except cls.DoesNotExist:
            return HttpResponse(status=404)

        success = bot.unregister()

        return JsonResponse({
            'success': success
        })

    @classmethod
    def register_or_update_bot_from_view(cls, request, application, **kwargs):
        """
        Регистрация бота из view

        :param request: запрос, полученный из приложения bitrix
        :param application: bitrix_app бота
        :param kwargs: необязательные поля бота
        :return: зарегистрированный бот
        """

        author = cls.__get_bx_user_from_request(request)

        try:
            bot = cls.objects.get(author__portal__domain=author.portal.domain)

        except cls.DoesNotExist:
            bot = cls()

        bot.__assign_fields(application=application, **kwargs)

        if not bot.author_id:
            bot.author = author

        if not bot.is_active:
            bot.register()

        else:
            bot.update()

        return bot

    def __assign_fields(self, **kwargs):
        for arg in kwargs:
            if arg != 'avatar':
                setattr(self, arg, kwargs[arg])
