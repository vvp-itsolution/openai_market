import logging
import telegram
from typing import Union

from django.contrib import admin
from integration_utils.vendors.telegram import InlineKeyboardMarkup, InlineKeyboardButton

from its_utils.app_telegram_bot.models.abstract_bot import AbstractBot
from bitrix_utils.bitrix_auth.models import BitrixApp
from bitrix_utils.bitrix_telegram_log.models import (
    TelegramUser,
    TelegramChat,
    TelegramMessage,
    PortalChat,
    LogBotApp,
)


class LogBotAppInline(admin.TabularInline):
    model = LogBotApp
    fields = 'app',
    extra = 0


class TelegramLogBot(AbstractBot):
    USER_CLASS = TelegramUser
    CHAT_CLASS = TelegramChat
    MESSAGE_CLASS = TelegramMessage

    RAISE_CHAT_MIGRATED_ERROR = True
    RAISE_UNAUTHORIZED_ERROR = True

    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }

    class Meta:
        app_label = 'bitrix_telegram_log'

    class Admin(AbstractBot.Admin):
        inlines = LogBotAppInline,

    @classmethod
    def get_for_app(cls, app: Union[str, BitrixApp]) -> 'TelegramLogBot':
        bot_app_qs = LogBotApp.objects.filter(bot__is_active=True)
        bot_app = bot_app_qs.get(app__name=app) if isinstance(app, str) else bot_app_qs.get(app=app)
        return bot_app.bot

    def on_start_command(self,
                         message: telegram.Message,
                         t_user: TelegramUser,
                         t_chat: TelegramChat,
                         param: str):

        try:
            portal_chat = PortalChat.objects.get(secret=param)
        except PortalChat.DoesNotExist:
            return

        PortalChat.objects.filter(chat=t_chat).update(chat=None)

        portal_chat.chat = t_chat
        portal_chat.save(update_fields=['chat'])
        self.send_message(t_chat.telegram_id, 'Чат привязан')

    def on_level_command(self,
                         message: telegram.Message,
                         t_user: TelegramUser,
                         t_chat: TelegramChat,
                         param: str):

        try:
            portal_chat = PortalChat.objects.get(chat=t_chat)
        except PortalChat.DoesNotExist:
            return

        param = param.upper()
        level = self.LOG_LEVELS.get(param)

        if level:
            portal_chat.level = self.LOG_LEVELS.get(param)
            portal_chat.save()
            self.send_message(message.chat.id, 'В чат будут попадать записи уровня {} и выше'.format(
                param
            ))

        else:
            self.send_message(
                chat_id=message.chat.id,
                text='Выберите уровень логирования',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(level, callback_data='/level {}'.format(level))]
                    for level
                    in self.LOG_LEVELS.keys()
                ])
            )

    def on_info_command(self,
                        message: telegram.Message,
                        t_user: TelegramUser,
                        t_chat: TelegramChat,
                        param: str):

        # айди чата Б24
        # Адрес портала к которому привязано
        # app.code приложения к котормоу привязано

        try:
            portal_chat = PortalChat.objects.get(chat=t_chat)
        except PortalChat.DoesNotExist:
            portal_chat = None

        self.send_message(
            chat_id=message.chat.id,
            parse_mode='HTML',
            text=(
                '<b>ID чата:</b> {}\n'
                '<b>Портал:</b> {}\n'
                '<b>app.code:</b> {}'
            ).format(
                message.chat.id,
                portal_chat.portal.domain if portal_chat else 'не привязан',
                portal_chat.app.name if portal_chat else '-'
            ),
        )

    def on_mute_command(self,
                        message: telegram.Message,
                        t_user: TelegramUser,
                        t_chat: TelegramChat,
                        param: str):
        try:
            portal_chat = PortalChat.objects.get(chat=t_chat)
        except PortalChat.DoesNotExist:
            return

        param = param.strip()
        if not param:
            self.send_message(message.chat.id, 'Необходимо передать тип события')
            return

        portal_chat.mute_log_type(param)
        self.send_message(
            message.chat.id, 'События типа #{} <b>не будут</b> попадать в лог'.format(param),
            parse_mode=self.HTML_PARSE_MODE,
        )

    def on_unmute_command(self,
                          message: telegram.Message,
                          t_user: TelegramUser,
                          t_chat: TelegramChat,
                          param: str):

        try:
            portal_chat = PortalChat.objects.get(chat=t_chat)
        except PortalChat.DoesNotExist:
            return

        param = param.strip()
        if not param:
            self.send_message(message.chat.id, 'Необходимо передать тип события')
            return

        portal_chat.unmute_log_type(param)
        self.send_message(
            message.chat.id, 'События типа #{} <b>будут</b> попадать в лог'.format(param),
            parse_mode=self.HTML_PARSE_MODE,
        )

    def on_kick(self,
                message: telegram.Message,
                t_user: TelegramUser,
                t_chat: TelegramChat):
        try:
            portal_chat = PortalChat.objects.get(chat=t_chat)
        except PortalChat.DoesNotExist:
            return

        portal_chat.chat = None
        portal_chat.save(update_fields=['chat'])
