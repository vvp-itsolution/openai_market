from django.contrib import admin
from django.db import models


class LogBotApp(models.Model):
    app = models.OneToOneField(
        'bitrix_auth.BitrixApp',
        on_delete=models.PROTECT,
    )

    bot = models.ForeignKey(
        'bitrix_telegram_log.TelegramLogBot',
        on_delete=models.PROTECT,
    )

    class Meta:
        app_label = 'bitrix_telegram_log'

    class Admin(admin.ModelAdmin):
        pass

    def __str__(self):
        return '{} - {}'.format(self.app, self.bot)
