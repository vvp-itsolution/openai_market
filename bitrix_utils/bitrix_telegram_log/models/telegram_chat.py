from django.db import models
from its_utils.app_telegram_bot.models.abstract_chat import AbstractChat


class TelegramChat(AbstractChat):
    bot = models.ForeignKey(
        'bitrix_telegram_log.TelegramLogBot',
        on_delete=models.PROTECT,
    )

    class Meta:
        app_label = 'bitrix_telegram_log'
