from django.db import models

from its_utils.app_telegram_bot.models.abstract_chat_participant import AbstractChatParticipant


class TelegramChatParticipant(AbstractChatParticipant):
    chat = models.ForeignKey(
        'bitrix_telegram_log.TelegramChat',
        related_name='participants',
        on_delete=models.CASCADE,
    )

    user = models.ForeignKey(
        'bitrix_telegram_log.TelegramUser',
        related_name='participated_chats',
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = 'chat', 'user'
        app_label = 'bitrix_telegram_log'
