Модуль для подключения евентов к приложениям Б24

1) Создать проект похожий на example_event_collector
настроить переменные в классе настроек
APPLICATION_NAME = 'local.5d62deeb187727.91972849'
EVENT_LIST = FULL_EVENT_LIST
EVENT_MODEL = CollectorBitrixEvent

2) Прописать его в инсталлед аппс 'bitrix_utils.bitrix_events.example_event_collector',

3) Прописать urls
from bitrix_utils.bitrix_events.example_event_collector.models import PortalEventSetting
path('event_collector/', include(PortalEventSetting.urls())),


4) Прописать кроны
1. Крон который проверяет подписки на события
 bitrix_utils.bitrix_events.crons.cron_check_all_portals_subscriptions.cron_check_all_portals_subscriptions
раз в 10 минут с параметром {"class_path":"bitrix_utils.bitrix_events.example_event_collector.models.portal_events_setting.PortalEventSetting"}
2. Крон который получает офлайн события и записывает в модель Событий
bitrix_utils.bitrix_events.crons.cron_collect_bitrix_events.cron_collect_bitrix_events
раз в 5 секунд с параметром {"class_path":"bitrix_utils.bitrix_events.example_event_collector.models.portal_events_setting.PortalEventSetting"}