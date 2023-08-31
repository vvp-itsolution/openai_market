from typing import TYPE_CHECKING

from telethon.tl.custom import Message as TlMessage

from django.contrib import admin
from django.db import models

if TYPE_CHECKING:
    from its_utils.app_telethon.models import BaseUser, BaseDialog


class BaseMessage(models.Model):
    dialog = models.ForeignKey('TelethonDialog', on_delete=models.PROTECT)
    sender = models.ForeignKey('TelethonUser', on_delete=models.PROTECT)
    message_id = models.IntegerField()
    reply_to_msg_id = models.IntegerField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    raw_text = models.TextField(null=True, blank=True)
    out = models.BooleanField()
    dt = models.DateTimeField()

    class Meta:
        unique_together = 'dialog', 'sender', 'message_id'
        abstract = True

    class Admin(admin.ModelAdmin):
        list_display = 'dialog', 'sender', 'dt',
        list_display_links = list_display
        raw_id_fields = 'dialog', 'sender',
        search_fields = 'dialog__session__session_id', 'dialog__dialog_id', 'sender__user_id', 'sender__username',

    def __str__(self):
        return str(self.message_id)

    @classmethod
    def from_tl_chat(cls, dialog: 'BaseDialog', sender: 'BaseUser', tl_message: TlMessage) -> 'BaseMessage':
        message, _ = cls.objects.get_or_create(
            dialog=dialog,
            sender=sender,
            message_id=tl_message.id,
            defaults=dict(
                text=tl_message.text,
                raw_text=tl_message.raw_text,
                dt=tl_message.date,
                out=tl_message.out,
                reply_to_msg_id=tl_message.reply_to_msg_id,
            )
        )

        update_fields = []

        if message.text != tl_message.text:
            message.text = tl_message.text
            update_fields.append('text')

        if update_fields:
            message.save(update_fields=update_fields)

        return message

    def to_dict(self) -> dict:
        return dict(
            id=self.message_id,
            out=self.out,
            dt=self.dt,
            sender_id=self.sender_id,
            text=self.text,
        )
