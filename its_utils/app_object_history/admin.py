# coding=utf-8

from __future__ import unicode_literals

from django.contrib import admin

from its_utils.app_object_history.models import ObjectHistory


@admin.register(ObjectHistory)
class ObjectHistoryRecordAdmin(admin.ModelAdmin):
    list_display = 'time', 'content_type', 'content_object'
    list_display_links = list_display
    list_filter = 'content_type',
    raw_id_fields = 'content_type',
