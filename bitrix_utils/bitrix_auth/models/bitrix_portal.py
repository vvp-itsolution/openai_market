# -*- coding: utf-8 -*-
import pprint
from six import (
    itervalues,
    python_2_unicode_compatible,
    string_types, integer_types,
)

from django.core.cache import cache
from django.db import models
from django.utils import timezone

import settings
from its_utils.app_admin.get_admin_url import get_admin_a_tag
from integration_utils.bitrix24.functions.api_call import api_call
from .bitrix_department import BitrixDepartment
from .bitrix_user_token import BitrixUserToken

from settings import ilogger

if False:
    # for type annotations
    from typing import List, Optional, Sequence
    from . import BitrixUser
    from .bitrix_user_token import BitrixApiError


def _sort_by_sort(lst): return sorted(lst, key=lambda o: o['sort'])


class ExtranetViolation(RuntimeError):
    pass


missing = object()


@python_2_unicode_compatible
class BitrixPortal(models.Model):

    domain = models.CharField(max_length=255)
    member_id = models.CharField(max_length=32)
    joined = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    scope = models.TextField(blank=True, default='')

    log_post_id = models.IntegerField(null=True, blank=True)

    class Meta:
        app_label = 'bitrix_auth'

    if getattr(settings, 'IS_ROOT_APP', False):
        class DeferedFieldManager(models.Manager):

            def __init__(self, defered_fields=[]):
                super().__init__()
                self.defered_fields = defered_fields

            def get_queryset(self, *args, **kwargs):
                return super().get_queryset(*args, **kwargs).defer(*self.defered_fields)

        objects = DeferedFieldManager(["log_post_id"])
        Meta.base_manager_name = 'objects'



    def __str__(self):
        return self.domain

    def random_token(self, application_names=None, is_admin=None, using=None):
        # type: (Sequence[str], Optional[bool], Optional[str]) -> BitrixUserToken
        return BitrixUserToken.get_random_token_for_apps(
            application_names=application_names,
            portal_id=self.id,
            is_admin=is_admin,
            using=using,
        )

    def root_departments(self):
        """Возвращает корневые отделы, ориентируется только на данные в нашей БД
        """
        return BitrixDepartment.portal_roots(self.id)

    def check_is_active(self, application_name):
        # type: (str) -> bool
        """Проверяет активен ли портал, запрашивает метод app.info

        NB! Пока не переключает поле BitrixPortal.active,
        чтобы случайно не поотрубать рабочие порталы.
        """
        from . import BitrixUserToken
        try:
            token = self.random_token(application_names=[application_name])
        except BitrixUserToken.DoesNotExist:
            return False
        try:
            token.call_list_method_v2('app.info')
        except BitrixApiError as e:
            if e.is_connection_to_bitrix_error or \
                    e.is_error_connecting_to_authorization_server or \
                    e.is_internal_server_error:
                # Такие ошибки скорее всего говорят о том, что портал
                # недоступен/упал, поэтому мы не можем знать установлено ли
                # на нем приложение, лучше кинем ошибку
                raise
            # Прочие ошибки (типа деактивации токена)
            # почти наверняка означают удаление приложения,
            # но можно дополнительно поизучать этот вопрос
            return False
        else:
            return True

    def get_department_tree(self, token, max_age_sec=30*60,
                            update_departments=True):
        # type: (BitrixUserToken, Optional[int], bool) -> List[dict]
        """Получение структуры компании от битрикса:

        Returns:
            [{
                'id': 1,
                'name': 'Моя компания',
                'sort': 500,
                'head_id': 1,  # Битриксовый ID главы отдела или None
                'parent_id': None,
                'children': [
                    {
                        'id': 42,
                        'name': 'Бухгалтерия',
                        'sort': 500,
                        'head_id': 12,  # Битриксовый ID главы отдела или None
                        'parent_id': 1,
                        'children': [],
                    },
                ],
            }]

        NB! корневых разделов может быть несколько

        :type token: BitrixUserToken
        :param max_age_sec: сколько считать данные свежими
        :param update_departments: обновить записи BitrixDepartment
        """
        portal_id = token.user.portal_id
        last_update_key = 'department-tree-updated-portal#%d' % portal_id
        if max_age_sec is not None:
            last_update = cache.get(last_update_key)
            if last_update is not None and \
                    (timezone.now() - last_update).seconds <= max_age_sec:
                root_deps = self.root_departments()
                if root_deps:
                    return [root_dep.tree() for root_dep in root_deps]
        bx_response = token.call_list_method_v2('department.get')
        departments = dict((int(bx_department['ID']), dict(
            id=int(bx_department['ID']),
            name=bx_department['NAME'],
            sort=int(bx_department['SORT']),
            head_id=int(bx_department['UF_HEAD'])
            if bx_department.get('UF_HEAD') else None,
            parent_id=int(bx_department['PARENT'])
            if bx_department.get('PARENT') else None,
            children=[],
        )) for bx_department in bx_response)
        roots = []
        for department in _sort_by_sort(itervalues(departments)):
            parent_id = department['parent_id']
            if parent_id is None:
                roots.append(department)
            else:
                departments[parent_id]['children'].append(department)
        if not roots:
            raise RuntimeError('no root department')
        if update_departments:
            ilogger.debug('BitrixDepartment_update_from_tree',
                          pprint.pformat([portal_id, roots], 2, 120))
            BitrixDepartment.update_from_tree(portal_id, roots)
            cache.set(last_update_key, timezone.now(), None)
        return roots

    def create_user_by_id(self, bitrix_id, token, extranet_ok=False):
        # type: (int, BitrixUserToken, bool) -> BitrixUser
        """Создает запись BitrixUser для данного портала.
        """
        from .bitrix_user import BitrixUser
        assert token.user.is_admin

        bitrix_user = self.bitrix_user.filter(bitrix_id=bitrix_id).first()
        if bitrix_user:
            return bitrix_user

        try:
            user = self.get_users(token, bx_id=bitrix_id)[0]
        except IndexError as e:
            raise BitrixUser.DoesNotExist from e
        else:
            assert int(user['ID']) == int(bitrix_id)

        if not extranet_ok and (
                not user['UF_DEPARTMENT'] or user['UF_DEPARTMENT'] == [0]):
            raise ExtranetViolation('extranet user')

        bitrix_user = BitrixUser()
        bitrix_user.portal = self
        bitrix_user.update_from_bx_response(user, save=True)
        return bitrix_user

    def get_users(self, token, policy='hard-exclude', bx_id=None,
                  bx_filter=None, active=missing, call_list=None,
                  update_local_users=True,
                  **kwargs):
        """Возвращает список пользователей на портале,
        выполняет запрос к users.get REST-API Б24.

        NB! нормализует UF_DEPARTMENT пользователей, приводя к списку

        Usage:
            Активные, без экстранета, без ботов:
                portal.get_users(token, 'hard-exclude')
            Активные+уволенные, без экстранета, без ботов:
                portal.get_users(token, 'hard-exclude', active=None)
            Активные+уволенные с экстранетом и ботами:
                portal.get_users(admin_token, 'all', active=None)
            Пользователи по id:
                portal.get_users(token, bx_id=[1, 2, 3])
                portal.get_users(token, bx_id=42)
            Поиск по имени:
                portal.get_users(tok, bx_filter=dict(
                    NAME_SEARCH='Маша Иванова',
                ))

        :type token: BitrixUserToken

        :type policy: str
        :param policy: какие пользователи включаются в ответ:
            'soft-exclude' - только нормальные пользователи портала,
            без экстранетных, на коробке также могут вернуться чатботы :-(
            'hard-exclude' - аналогично soft_exclude, но
            на коробке эвристиками пытаемся удалить чатботов из выдачи
            'employee-extranet' - сотрудники + экстранетчики,
            без чатботов
            'all' - включить всех, NB! требует админского токена,
            по-факту на облаке чатботы все равно не возвращаются,
            зато есть экстранет, на коробке не проверял,
            скорее всего вернутся и экстранет-пользователи и боты

        :param bx_id: опционально id пользователя или список id
            NB! при передаче id+фильтров битрикс игнорирует id,
            так что метод нельзя вызвать с обоими параметрами
            NB! при передаче id полностью игнорируются проверки
            активности, экстранета, ботов и пр.
        :param bx_filter: см. user.get параметр FILTER
            https://dev.1c-bitrix.ru/rest_help/users/user_get.php
            NB! не работает при передаче id
        :param active:
            None - уволенные и активные
            True - активные (по умолч.)
            False - уволенные
            NB! не работает при передаче id
        :param call_list: использовать call_list_method, по умолч.
            call_api_method используется при передаче от 1 до 50 bx_id,
            во всех других случаях используется call_list_method
        :param update_local_users: Обновить информацию о полученных
            пользователях в нашей БД
        :param kwargs: kwargs для BitrixPortal.get_department_tree
            для отсеивания чатботов по подразделам на коробках,
            актуально только при policy='hard-exclude'

        :rtype: list[dict]
        :raises: CallListException при call_list=True
        :raises: BitrixApiError при call_list=False
        """
        from .bitrix_department import BitrixDepartment
        from .bitrix_user import BitrixUser

        assert token.user.portal_id == self.id, 'wrong token'
        assert policy in (
            'soft-exclude', 'hard-exclude', 'employee-extranet', 'all',
        ), 'wrong policy'
        assert bx_id is None or bx_filter is None, \
            'bx_id+bx_filter несовместимы, см. help() метода'
        assert 'ACTIVE' not in (bx_filter or {}), 'use `active` arg'

        if policy in ('employee-extranet', 'all',) and \
                not token.user.is_admin:
            # Если передать ADMIN_MODE=true не от админского токена,
            # то он будет проигнорирован. Лучше сразу кинуть тут ошибку
            raise RuntimeError("admin token required to get all/extranet users")

        params = dict(ADMIN_MODE='true'
                      if policy in ('employee-extranet', 'all',)
                      else 'false')
        if bx_id is not None:
            if not isinstance(bx_id, string_types + integer_types):
                bx_id = list(bx_id)
            params['ID'] = bx_id
            if active is not missing:
                raise RuntimeError('active игнорируется при передаче bx_id')
            if call_list is None:
                call_list = not (
                    isinstance(bx_id, string_types + integer_types) or
                    len(bx_id) <= 50
                )
        if bx_filter is not None:
            params['FILTER'] = bx_filter
        if active is not None and bx_id is None:
            if active is missing:
                active = True
            params.setdefault('FILTER', {})
            params['FILTER']['ACTIVE'] = 'Y' if active else 'N'

        if call_list or call_list is None:
            users = token.call_list_method_v2('user.get', params)
        else:
            users = token.call_api_method('user.get', params, v=2)['result']
        BitrixDepartment.normalize_uf_departments(users)
        if update_local_users:
            bx_users_lookup = dict((int(u['ID']), u) for u in users)
            local_users = BitrixUser.objects.filter(
                portal=self,
                bitrix_id__in=bx_users_lookup.keys(),
            )
            for user in local_users:
                user.update_from_bx_response(bx_users_lookup[user.bitrix_id])
        if bx_id is not None:
            return users
        if policy in ('hard-exclude', 'soft-exclude',):
            # Дополнительно убираем экстранет пользователей,
            # если API решило по хз какой причине их вернуть
            # (вроде как некоторые коробки этим грешат)
            # Экстранет пользователи - пользователи с пустыми департаментами
            # и sic! департаментом [0] (такая хрень бывает у интеграторов)
            users = [u for u in users
                     if u['UF_DEPARTMENT'] and u['UF_DEPARTMENT'] != [0]]
        if policy in ('hard-exclude', 'employee-extranet',):
            # Убираем костылями чатботов на коробках
            return BitrixUser.exclude_chatbots(
                token=token,
                bx_portal=self,
                users=users,
                **kwargs
            )
        return users

    def is_box(self, token=None, application_names=None):
        """Возвращает коробочный ли портал на основании LICENSE из app.info

        :type token: BitrixUserToken
        :param application_names: для получения случайного токена

        :rtype: bool
        """
        assert token is not None or application_names is not None

        if hasattr(self, '_is_box'):
            return self._is_box

        if token is None:
            token = self.random_token(application_names)
        app_info = token.call_api_method('app.info')['result']
        # Пример LICENSE облака: 'ru_project'
        # Пример LICENSE коробки: 'ru_selfhosted'
        self._is_box = 'selfhosted' in app_info['LICENSE']
        return self._is_box

    def verify_online_event(self, application_name: str,
                            access_token: str, application_token: str) -> bool:
        """Проверка подлинности онлайн-события Б24, пример использования:
        bitrix_utils.bitrix_mirror.bitrix_mirror_main.views.online_event_handler

        Абсолютно аналогично проверяется и обработчик bizproc.activity.add
        Аналогично для bizproc.robot.add

        принцип проверки
        https://dev.1c-bitrix.ru/rest_help/general/events/event_safe.php
        если токен известен, то сверяем с БД
        если нет, то пробуем сделать app.info и сверяем app.info код приложения

        :param application_name: BitrixApp.name
        :param access_token: request.POST['auth[access_token]']
        :param application_token: request.POST['auth[application_token]']
        :return: True - событие корректное, False - некорректное событие
        """
        from .bitrix_app_installation import BitrixAppInstallation

        try:
            app_installation = BitrixAppInstallation.objects \
                .select_related('application') \
                .get(portal=self, application__name=application_name)
        except BitrixAppInstallation.DoesNotExist:
            ilogger.warning('verify_online_event_app_installation_not_found',
                            'for portal {}'.format(get_admin_a_tag(self)))
            return False

        # Нам известен application_token приложения на портале
        if app_installation.application_token:
            if app_installation.application_token == application_token:
                return True
            else:
                ilogger.warning('verify_online_event_token_do_not_match',
                                'for portal {}'.format(get_admin_a_tag(app_installation, self.domain)))
                return False

        # application_token неизвестен, проверяем переданный access_token
        resp = api_call(self.domain, 'app.info', auth_token=access_token, timeout=1)
        try:
            token_valid = resp.ok and \
                    resp.json()['result']['CODE'] == application_name
        except ValueError:
            token_valid = False

        if not token_valid:
            # access_token видимо неверный
            ilogger.warning('verify_online_event_token_not_valid',
                            'for portal {}'.format(get_admin_a_tag(app_installation, self.domain)))
            return False

        # access_token верный, сохраняем application_token
        app_installation.application_token = application_token
        app_installation.save(update_fields=['application_token'])
        return True

    def blogpost_log(
            self,
            bx_token,   # type: BitrixUserToken
            message,  # type: str
    ):
        """
        Отправить сообщение об ошибке в живую ленту

        https://b24.it-solution.ru/company/personal/user/50/tasks/task/view/7021/
        1. Создает пост если его еще нет и запоминает в модели "bitrix_portal" его айди
        2. Добавляет комментарий с логом
        3. Контроллирует что все админы являются получателями
        """

        from . import BitrixUser

        # админов можем получить только из бд
        admins = BitrixUser.objects.filter(portal=self, is_admin=True)
        dest = ['U{}'.format(admin.bitrix_id) for admin in admins]

        try:
            if self.log_post_id:
                existed_post = bx_token.call_api_method('log.blogpost.get', {'POST_ID': self.log_post_id})['result']
                if not existed_post:
                    # пост удалён - создать новый
                    self.log_post_id = None

                else:
                    # убедиться, что все админы подключены к посту
                    bx_token.call_api_method('log.blogpost.share', {
                        'POST_ID': self.log_post_id,
                        'DEST': dest,
                    })

            if not self.log_post_id:
                # создать новый пост и сохранить id
                self.log_post_id = bx_token.call_api_method('log.blogpost.add', {
                    'POST_TITLE': 'Сообщения об ошибках приложений',
                    'POST_MESSAGE': 'В комментарии будут попадать сообщения об ошибках',
                    'DEST': dest,
                })['result']
                self.save(update_fields=['log_post_id'])

            # добавить комментарий с сообщением об ошибке
            bx_token.call_api_method('log.blogcomment.add', {
                'POST_ID': self.log_post_id,
                'TEXT': '{message}\n\n[URL=https://{domain}/marketplace/app/{app}/]Открыть приложение[/URL]'.format(
                    message=message,
                    domain=self.domain,
                    app=bx_token.application.name,
                ),
            })

        except Exception as exc:
            ilogger.error('blogpost_log_failed', 'at {}: {}\n{}'.format(
                self.domain, exc, message
            ))
