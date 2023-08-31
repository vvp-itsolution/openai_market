from bitrix_utils.bitrix_events.admin import AbsPortalEventSettingAdmin
from bitrix_utils.bitrix_events.constants import CRM_EVENT_LIST
from bitrix_utils.bitrix_events.models.abs_portal_events_setting import AbsPortalEventSetting
from ..models import CollectorBitrixEvent
from django.contrib import admin


class PortalEventSetting(AbsPortalEventSetting):

    APPLICATION_NAME = 'local.5d62deeb187727.91972849'
    EVENT_LIST = CRM_EVENT_LIST
    EVENT_MODEL = CollectorBitrixEvent
    BITRIX_ONLINE_EVENT_HANDLER = 'https://mirror3.it-solution.ru/event_collector/event_handler/'


    class Meta:
        app_label = 'example_event_collector'
        verbose_name = u'Настройки портала'
        verbose_name_plural = u'Настройки порталов'


admin.site.register(PortalEventSetting, AbsPortalEventSettingAdmin)
