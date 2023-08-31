# coding: utf-8

from __future__ import unicode_literals

from django.contrib import admin

from bitrix_utils.bitrix_events.admin import AbsBitrixEventAdmin
from bitrix_utils.bitrix_events.models.abs_bitrix_event import AbsBitrixEvent


class CollectorBitrixEvent(AbsBitrixEvent):

    class Meta:
        app_label = 'example_event_collector'


admin.site.register(CollectorBitrixEvent, AbsBitrixEventAdmin)
