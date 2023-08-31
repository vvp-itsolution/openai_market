# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import reduce

from django.db import models
from django.utils import timezone
import six

from its_utils.app_admin.action_admin import ActionAdmin
from its_utils.app_admin.json_admin import JsonAdmin

if False:
    from bitrix_utils.bitrix_auth.models import BitrixUserToken

if not six.PY2:
    from typing import Optional, Sequence

from its_utils.functions.compatibility import get_json_field

JSONField = get_json_field()


@six.python_2_unicode_compatible
class AbsBitrixEvent(models.Model):
    """Оффлайн-событие, полученное от Б24
    """
    portal = models.ForeignKey('bitrix_auth.BitrixPortal', on_delete=models.CASCADE)
    event_name = models.CharField(max_length=127, default='')
    data = JSONField(default=dict)
    datetime = models.DateTimeField(default=timezone.now)

    # bitrix_id = models.IntegerField(null=True, blank=True)

    from its_utils.django_postgres_fuzzycount.fuzzycount import FuzzyCountManager
    objects = FuzzyCountManager()

    class Meta:
        abstract = True
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    class Admin(ActionAdmin, JsonAdmin):
        list_display = (
            'portal', 'event_name', 'datetime', 'user_id',
        )

        list_display_links = list_display
        list_filter = ['portal', 'event_name']


    def __str__(self):
        return '[{}][{}] {}'.format(self.portal, self.id, self.event_name)

    def get_token(self, application_names, is_admin=None, using=None):
        # type: (Sequence[str], Optional[bool], Optional[str]) -> Optional[BitrixUserToken]
        """Возвращает токен для запросов к api

        application_names: подходящие коды приложения, например: 'itsolutionru.kdb'
        is_admin: админский ли нужен токен? None - не важно какой
        using: https://docs.djangoproject.com/en/3.0/topics/db/multi-db/#manually-selecting-a-database-for-a-queryset
        """
        return self.portal.random_token(
            application_names=application_names,
            is_admin=is_admin,
            using=using,
        )

    def user_id(self):  # type: () -> Optional[int]
        """Пользователь, инициировавший событие передается
        в EVENT_ADDITIONAL['user_id']

        NB! соответствует BitrixUser.bitrix_id пользователя
        """
        if self.event_name.upper() == 'ONUSERADD':
            # Событие добавления пользователя по факту срабатывает,
            # когда новый пользователь заходит на портал, так что можно считать
            # это событием "подтверждением регистрации" от нового пользователя.
            # В этом случае он сам является инициатором действия, а не тот
            # человек, который пригласил его на портал
            return int(self.data['EVENT_DATA']['ID'])

        user_id_paths = (
            ['EVENT_DATA', 'USER_ID'],
            ['EVENT_DATA', 'PORTAL_USER_ID'],
            ['EVENT_ADDITIONAL', 'user_id'],
        )
        for path in user_id_paths:
            try:
                user_id = int(reduce(dict.__getitem__, path, self.data))
                break
            except (KeyError, TypeError, ValueError):
                pass
        else:
            return

        if user_id == 0:
            # У некоторых событий бывает вот такая хрень
            return 0
        elif user_id:
            return int(user_id)
    user_id.short_description = 'bitrix_id пользователя'
    user_id = property(user_id)
