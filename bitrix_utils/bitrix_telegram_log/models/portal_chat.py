import logging
import uuid
from typing import Union

from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from integration_utils.vendors.telegram.error import Unauthorized, BadRequest, ChatMigrated

from bitrix_utils.bitrix_auth.models import BitrixPortal, BitrixApp
from its_utils.app_admin.action_admin import ActionAdmin

from settings import ilogger

from its_utils.functions.compatibility import get_json_field

JSONField = get_json_field()


class PortalChat(models.Model):
    portal = models.ForeignKey(
        'bitrix_auth.BitrixPortal',
        on_delete=models.PROTECT,
    )

    app = models.ForeignKey(
        'bitrix_auth.BitrixApp',
        on_delete=models.PROTECT,
    )

    chat = models.OneToOneField(
        'bitrix_telegram_log.TelegramChat',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    secret = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
    )

    level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    status_message_id = models.IntegerField(
        null=True,
        blank=True,
    )

    # дата отправки сообщения со статусом (отправляем новое сообщение, если были сообщения лога)
    status_message_dt = models.DateTimeField(
        default=timezone.now,
    )

    # дата обновления сообщения со статусом (следим за таймаутом)
    status_message_update_dt = models.DateTimeField(
        default=timezone.now,
    )

    last_log_dt = models.DateTimeField(
        default=timezone.now,
    )

    muted_log_types = JSONField(default=list, null=True, blank=True)

    class Meta:
        unique_together = 'portal', 'app'
        app_label = 'bitrix_telegram_log'

    class Admin(ActionAdmin):
        raw_id_fields = 'portal', 'chat'
        actions = 'ping',

    def __str__(self):
        return '[{}] {}'.format(self.chat_id, self.portal)

    @classmethod
    def get_for_portal(cls, portal: BitrixPortal, app: Union[str, BitrixApp]) -> 'PortalChat':
        if isinstance(app, str):
            app = BitrixApp.objects.get(name=app)

        portal_chat, _ = cls.objects.get_or_create(portal=portal, app=app)
        return portal_chat

    @cached_property
    def bot(self):
        from bitrix_utils.bitrix_telegram_log.models import TelegramLogBot
        return TelegramLogBot.get_for_app(self.app)

    @property
    def status_updated_seconds_ago(self) -> float:
        return (timezone.now() - self.status_message_update_dt).total_seconds()

    def get_required_level(self) -> int:
        return self.level or logging.NOTSET

    def get_bind_url(self):
        return 'https://telegram.me/{username}?startgroup={secret}'.format(
            username=self.bot.username,
            secret=self.secret.hex,
        )

    def log(self, level: int, log_type: str, message: str, tag: str = None):
        text = '#{level} #{type} {tag}\n{message}'.format(
            level=logging.getLevelName(level),
            type=log_type,
            tag='#{}'.format(tag) if tag else '',
            message=message,
        )

        try:
            self.bot.send_message(chat_id=self.chat.telegram_id, text=text, parse_mode='HTML')

        except ChatMigrated as exc:
            from bitrix_utils.bitrix_telegram_log.models import TelegramChat
            self.chat, _ = TelegramChat.objects.get_or_create(telegram_id=exc.new_chat_id, bot=self.bot)
            self.save(update_fields=['chat'])
            return self.log(level=level, log_type=log_type, message=message, tag=tag)

        except Unauthorized:
            # бот не состоит в группе
            self.chat = None
            self.save(update_fields=['chat'])
            ilogger.info(
                'telegram_portal_log_bot_kicked',
                'bot {} kicked from group on portal {}'.format(
                    self.bot, self.portal,
                ),
            )

        self.last_log_dt = timezone.now()
        self.save(update_fields=['last_log_dt'])

    def status(self, text: str, max_frequency: int = 0) -> bool:
        """
        Обновить сообщение статуса в чате

        :param text: текст сообщения
        :param max_frequency: если сообщение обновлялось меньшее количество секунд, чем указано в параметре,
                              обновление не произойдёт
        :return: True, если сообщение обновлено; False, если произошла ошибка или достигли таймаута
        """

        if self.status_updated_seconds_ago < max_frequency:
            # https://b24.it-solution.ru/company/personal/user/50/tasks/task/view/14070/
            return False

        if self.status_message_id:
            if self.last_log_dt > self.status_message_dt:
                # были залогированные сообщения - удаляем старое сообщение, отправляем новое

                try:
                    self.bot.client.delete_message(
                        chat_id=self.chat.telegram_id,
                        message_id=self.status_message_id,
                    )

                except BadRequest:
                    pass

                except Exception as exc:
                    ilogger.warning(
                        'telegram_portal_log_status',
                        'failed to delete status message at {}: {}'.format(
                            self.portal, exc,
                        ),
                    )

                self.status_message_id = None

            else:
                # логов не было - обновляем старое сообщение

                try:
                    self.bot.edit_message(
                        chat_id=self.chat.telegram_id,
                        message_id=self.status_message_id,
                        parse_mode='HTML',
                        text='{}\n\n<i>Обновлено в {}</i>'.format(
                            text, timezone.localtime().strftime('%H:%M'),
                        )
                    )

                except BadRequest:
                    self.status_message_id = None

                except Exception as exc:
                    ilogger.error(
                        'telegram_portal_log_status',
                        'failed to edit status message at {}: {}'.format(
                            self.portal, exc,
                        )
                    )
                    return False

        now = timezone.now()
        if not self.status_message_id:
            try:
                message = self.status_message_id = self.bot.send_message(
                    chat_id=self.chat.telegram_id,
                    text=text,
                )
                if not message:
                    return False

                self.status_message_id = message.telegram_id
                self.status_message_dt = now

            except Exception as exc:
                ilogger.error(
                    'telegram_portal_log_status',
                    'failed to send status message at {}: {}'.format(
                        self.portal, exc,
                    )
                )
                return False

        self.status_message_update_dt = now
        self.save(update_fields=['status_message_id', 'status_message_dt', 'status_message_update_dt'])
        return True

    def ping(self):
        """
        :admin_action_description: ping chat
        """
        if not self.chat:
            return 'Чат не привязан'

        try:
            self.bot.client.send_message(
                chat_id=self.chat.telegram_id,
                text='Hello',
            )

        except (Unauthorized, BadRequest):
            self.chat = None
            self.save(update_fields=['chat'])
            return 'Чат не привязан'

        except Exception as exc:
            return 'Ошибка: {}'.format(exc)

        return 'Отправлено сообщение в чат'

    def is_muted_log_type(self, log_type: str) -> bool:
        return self.muted_log_types and log_type in self.muted_log_types

    def mute_log_type(self, log_type: str):
        if not isinstance(self.muted_log_types, list):
            self.muted_log_types = []

        if log_type not in self.muted_log_types:
            self.muted_log_types.append(log_type)
            self.save(update_fields=['muted_log_types'])

    def unmute_log_type(self, log_type: str):
        if not isinstance(self.muted_log_types, list):
            self.muted_log_types = []

        while log_type in self.muted_log_types:
            self.muted_log_types.remove(log_type)

        self.save(update_fields=['muted_log_types'])
