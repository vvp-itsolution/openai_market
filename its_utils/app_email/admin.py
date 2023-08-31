# coding: UTF-8

from django.contrib import admin
from django.utils.safestring import mark_safe

from its_utils.app_admin.action_admin import ActionAdmin
from its_utils.app_email.models import *


@admin.register(OutgoingEmail)
class OutgoingEmailAdmin(ActionAdmin):
    list_display = ['is_sent_soe', 'to_soe', 'sender_soe', 'from_soe', 'cc_soe', 'bcc_soe']
    list_display_links = list_display
    actions = ["send"]


@admin.register(EmailSettings)
class EmailSettingsAdmin(admin.ModelAdmin):
    list_display = ['sender_email', 'host', 'username']
    list_display_links = list_display


@admin.register(MailTemplate)
class MailTemplateAdmin(admin.ModelAdmin):
    list_display = 'id', 'subject'
    list_display_links = list_display


@admin.register(TemplatedOutgoingMail)
class TemplatedOutgoingMailAdmin(ActionAdmin):
    list_display = 'template', 'from_email', 'to_email', 'date_create', 'date_sent', 'read'
    list_display_links = list_display
    raw_id_fields = 'template', 'from_email'
    readonly_fields = 'read', 'hash'

    actions = 'send_template',


@admin.register(MailImage)
class MailImageAdmin(admin.ModelAdmin):
    list_display = 'id', 'name', 'preview'
    list_display_links = list_display
    readonly_fields = 'preview',

    def preview(self, obj):
        return mark_safe('<img src="{}">'.format(
            obj.get_preview_url(100, 100)
        ))
