# -*- coding: utf-8 -*-
import six
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.db import models, transaction
from django.utils import timezone

from its_utils.functions.compatibility import get_null_boolean_field

NullBooleanField = get_null_boolean_field()


class NoGroupOnPortal(RuntimeError):
    def __init__(self, group_bitrix_id):
        self.id = group_bitrix_id
        message = 'no group #%d on portal' % group_bitrix_id
        super(NoGroupOnPortal, self).__init__(message)


@six.python_2_unicode_compatible
class BitrixGroup(models.Model):
    """Рабочая группа "соцсети" / проект
    """
    # https://dev.1c-bitrix.ru/rest_help/sonet_group/sonet_group_user_get.php
    MEMBER_ROLE_OWNER = 'A'
    MEMBER_ROLE_MODERATOR = 'E'
    MEMBER_ROLE_USER = 'K'
    MEMBER_ROLES = set((
        MEMBER_ROLE_OWNER,
        MEMBER_ROLE_MODERATOR,
        MEMBER_ROLE_USER,
    ))
    MEMBERS_CACHE_KEY_TEMPLATE = 'group-members-updated-group#{self.id}'
    NoneOnPortal = NoGroupOnPortal

    portal = models.ForeignKey('bitrix_auth.BitrixPortal', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    extranet = NullBooleanField(default=None, null=True)
    bitrix_id = models.IntegerField()

    # Список участников вида ['1-A', '42-K']
    members = ArrayField(models.CharField(max_length=64),
                         null=True, blank=True)

    class Meta:
        app_label = 'bitrix_auth'

    def __str__(self):
        return u'%s %s' % (self.portal, self.name)

    @property
    def cached_members(self):
        """Список участников группы (или None) из нашей БД

        :rtype: list[dict]
        :return: Список аналогичный методу get_members или None
        """
        if self.members is None:
            return None
        members = []
        for rec in self.members:
            id_, role = rec.split('-', 1)
            assert role in self.MEMBER_ROLES
            members.append(dict(id=int(id_), role=role))
        return members

    @property
    def _redis_cache_key(self):
        return self.MEMBERS_CACHE_KEY_TEMPLATE.format(self=self)

    def _get_members_updated(self):
        return cache.get(self._redis_cache_key)

    def _set_members_updated(self, when=None, expires=None):
        if when is None:
            when = timezone.now()
        cache.set(self._redis_cache_key, when, expires)

    def get_fresh_members(self, token, save=True):
        """Получить участников для группы. Всегда свежие данные от Б24.
        https://dev.1c-bitrix.ru/rest_help/sonet_group/sonet_group_user_get.php
        NB! REST-метод не дает получить участников для нескольких групп

        :type token: BitrixUserToken
        :param save: записать в БД

        :rtype: list[dict]
        Returns:
            [{'id': 1, 'role': 'A'}, {'id': 2, 'role': 'K'}]
            см. константы MEMBER_ROLE_* для описания ролей
        """
        assert token.user.portal_id == self.portal_id
        members = token.call_list_method_v2('sonet_group.user.get',
                                        dict(ID=self.bitrix_id))
        members = [dict(id=int(member['USER_ID']), role=member['ROLE'])
                   for member in members]
        self.members = ['{m[id]}-{m[role]}'.format(m=m) for m in members]
        self._set_members_updated()
        if save:
            self.save(update_fields=['members'])
        return members

    def get_members(self, token, save=True, max_age_sec=30*60):
        """Возвращает участников группы (закешированных или запрашивает у Б24)

        :type token: BitrixUserToken
        :param save: записать в БД
        :param max_age_sec: сколько считать полученные данные актуальными
        :rtype: list[dict]
        Returns:
            [{'id': 1, 'role': 'A'}, {'id': 2, 'role': 'K'}]
            см. константы MEMBER_ROLE_* для описания ролей
        """
        members_updated = self._get_members_updated()
        if self.members is None or members_updated is None or \
                (timezone.now() - members_updated).seconds > max_age_sec:
            return self.get_fresh_members(token, save=save)
        return self.cached_members

    def get(self, token, save=True):
        """Возвращает данные о группе:
        https://dev.1c-bitrix.ru/rest_help/sonet_group/sonet_group_get.php

        :type token: BitrixUserToken
        :param save: сохранить изменившееся название группы в БД
        :rtype: dict
        """
        assert token.user.portal_id == self.portal_id
        try:
            group_details = token.call_api_method('sonet_group.get', dict(
                FILTER=dict(ID=self.bitrix_id),
            ), v=2)['result'][0]
        except IndexError as e:
            six.raise_from(NoGroupOnPortal(self.bitrix_id), e)
            assert False
        self.name = group_details['NAME']
        # у групп нет поля IS_EXTRANET если в настройках портала
        # выключен сервис Экстранет, считаем такие группы интранетом
        self.extranet = group_details.get('IS_EXTRANET', 'N') == 'Y'
        if save:
            self.save()
        return group_details

    @classmethod
    def from_bitrix_id(cls, token, bitrix_id, get_data=None):
        """Создает запись на основании битрикс-id группы

        :type token: BitrixUserToken
        :param bitrix_id: id группы в Б24 на портале токена
        :type get_data: bool
        :param get_data: получить поля name, extranet методом sonet_group.get
            True - всегда получать и обновлять
            False - никогда не запрашивать
            None - (по умолч.) получить параметры для новой группы
            или если название/поле extranet пустое
        :rtype: tuple[BitrixGroup, dict, bool]
        :return: (
                <BitrixGroup #N>,
                <optional "sonet_group.get" response>,
                <created?>,
            )
        """
        with transaction.atomic():
            group, created = cls.objects.get_or_create(
                bitrix_id=bitrix_id,
                portal_id=token.user.portal_id,
            )
        details = None
        if get_data or (get_data is None and (
            created or
            group.name == '' or
            group.extranet is None
        )):
            details = group.get(token, save=True)
        return group, details, created
