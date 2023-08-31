1)

'bitrix_utils.bitrix_telegram_log',

2)
в urls.py
path('telegram_log/', include('bitrix_utils.bitrix_telegram_log.urls')),

3)migrate

4) Создаем бота через BotFather

5) Добавляем запись бота
from  bitrix_utils.bitrix_telegram_log.models import TelegramLogBot
TelegramLogBot.objects.create(username='b24hh_bot', auth_token='2025032770:AAEUpuVBkjuR222222222222222uQTPbATOvk', is_active=True)

4) Прописываем крон
from its_utils.app_cron.models import Cron
Cron.objects.create(name='Собития бота логгера', repeat_seconds=10, path='bitrix_utils.bitrix_telegram_log.cron.handle_bot_updates')

5)
/admin/bitrix_telegram_log/telegramlogbot/
модель бота, нужно указать BitrixApp, за которые он отвечает


6)
/admin/bitrix_telegram_log/portalchat/
модель портал/app/чат
log(level, log_type, message) отправляет сообщение в чат
get_bind_url()  формирует ссылку https://telegram.me/{username}?startgroup={secret}

bitrix_utils.bitrix_telegram_log.telegram_portal_logger.TelegramPortalLogger
класс логгера, который отправляет сообщения в чат


Использование
from bitrix_utils.bitrix_telegram_log.telegram_portal_logger import TelegramPortalLogger
TelegramPortalLogger(app='pycode', portal=self.portal, bx_app_names=[BX_APP_NAME])
TelegramPortalLogger.warn('warning_1', 'Текст варнинга')



bitrix_utils.bitrix_telegram_log.views.bind_portal.bind_portal
вьюха с кнопкой

Из браузера можно запустить привязку бота по ссылке
/telegram_log/btl/start_binding/?app=itsolutionru.bpstarter
app=itsolutionru.bpstarter передается, т.к на этому урле может быть много разных приложений