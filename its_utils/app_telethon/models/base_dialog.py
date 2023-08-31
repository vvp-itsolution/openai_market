import os
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib import admin
from django.db import models
from telethon.tl.custom import Dialog as TlDialog

from its_utils.app_telethon import dialog_types
from its_utils.app_telethon.telegram_client import TelegramClient

if TYPE_CHECKING:
    from its_utils.app_telethon.models import BaseSession


class BaseDialog(models.Model):
    TYPE_CHOICES = (
        (dialog_types.PRIVATE, dialog_types.PRIVATE),
        (dialog_types.GROUP, dialog_types.GROUP),
        (dialog_types.SUPERGROUP, dialog_types.SUPERGROUP),
        (dialog_types.CHANNEL, dialog_types.CHANNEL),
    )

    session = models.ForeignKey('TelethonSession', null=True, blank=True, on_delete=models.SET_NULL)
    dialog_id = models.BigIntegerField()
    dialog_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=dialog_types.PRIVATE)
    name = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    photo = models.FileField(null=True, blank=True)

    class Meta:
        unique_together = 'session', 'dialog_id'
        abstract = True

    class Admin(admin.ModelAdmin):
        list_display = 'session', 'dialog_id', 'dialog_type', 'name', 'username',
        list_display_links = list_display
        search_fields = 'session__session_id', 'name', 'username', 'dialog_id',
        raw_id_fields = 'session',

    def __str__(self):
        return '{}: [{}] {}'.format(self.session, self.dialog_id, self.name)

    @property
    def photo_url(self):
        return 'https://{}{}'.format(settings.DOMAIN, self.photo.url) if self.photo else None

    @classmethod
    def from_tl_dialog(cls, session: 'BaseSession', tl_dialog: TlDialog, client=None) -> 'BaseDialog':
        dialog_type = dialog_types.get_dialog_type(tl_dialog)
        username = getattr(tl_dialog.entity, 'username', None)

        dialog, _ = cls.objects.get_or_create(
            session=session,
            dialog_id=tl_dialog.id,
            defaults=dict(
                dialog_type=dialog_type,
                name=tl_dialog.name,
                username=username,
            )
        )

        update_fields = []

        if dialog.name != tl_dialog.name:
            dialog.name = tl_dialog.name
            update_fields.append('name')

        if dialog.username != username:
            dialog.username = username
            update_fields.append('username')

        if client and not dialog.photo:
            if dialog.download_photo(client):
                update_fields.append('photo')

        if update_fields:
            dialog.save(update_fields=update_fields)

        return dialog

    def to_dict(self) -> dict:
        return dict(
            id=self.dialog_id,
            title=self.name,
            username=self.username,
        )

    def download_photo(self, client: TelegramClient) -> bool:
        path = 'session{}/chat{}/photo.png'.format(
            self.session.id, self.dialog_id,
        )
        result = client.download_profile_photo(
            self.dialog_id, os.path.join(settings.MEDIA_ROOT, path), download_big=False,
        )
        if result:
            self.photo = path
            return True

        return False
