from its_utils.app_telegram_bot.models.abstract_user import AbstractUser


class TelegramUser(AbstractUser):
    class Meta:
        app_label = 'bitrix_telegram_log'
