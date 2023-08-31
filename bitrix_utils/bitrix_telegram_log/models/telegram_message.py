from django.db import models
from its_utils.app_telegram_bot.models.abstract_message import AbstractMessage


class TelegramMessage(AbstractMessage):
    chat = models.ForeignKey(
        'bitrix_telegram_log.TelegramChat',
        on_delete=models.CASCADE,
        related_name='history',
    )

    author = models.ForeignKey(
        'bitrix_telegram_log.TelegramUser',
        on_delete=models.CASCADE,
        null=True,
    )

    class Meta:
        app_label = 'bitrix_telegram_log'
