from typing import Union

from telethon.tl.types import User as TlUser, Channel as TlChannel
from telethon.tl.custom import Dialog as TlDialog

from django.contrib import admin
from django.db import models


class BaseUser(models.Model):
    user_id = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    is_bot = models.BooleanField(default=False)

    class Meta:
        abstract = True

    class Admin(admin.ModelAdmin):
        list_display = 'user_id', 'first_name', 'last_name', 'username', 'is_bot'
        list_display_links = list_display

    def __str__(self):
        return '{} {} {}'.format(
            self.first_name or "", self.last_name or "", f"@{self.username}" if self.username else "",
        )

    @classmethod
    def from_tl_user(cls, tl_user: Union[TlUser, TlChannel, TlDialog]) -> 'BaseUser':
        username = tl_user.username
        first_name = getattr(tl_user, 'first_name', getattr(tl_user, 'title', ''))
        last_name = getattr(tl_user, 'last_name', '')
        is_bot = getattr(tl_user, 'bot', False)

        user, _ = cls.objects.get_or_create(
            user_id=tl_user.id,
            defaults=dict(
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_bot=is_bot,
            )
        )

        update_fields = []

        if user.first_name != first_name:
            user.first_name = first_name
            update_fields.append('first_name')

        if user.last_name != last_name:
            user.last_name = last_name
            update_fields.append('last_name')

        if user.username != username:
            user.username = username
            update_fields.append('username')

        if update_fields:
            user.save(update_fields=update_fields)

        return user

    def to_dict(self) -> dict:
        return dict(
            id=self.user_id,
            first_name=self.first_name,
            last_name=self.last_name,
            username=self.username,
            is_bot=self.is_bot,
        )
