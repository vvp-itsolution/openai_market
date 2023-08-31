# -*- coding: utf-8 -*-
import six
import datetime

from django.db import models
from django.utils import timezone

from its_utils.app_admin.get_admin_url import get_admin_a_tag
from .bitrix_app import BitrixApp
from .bitrix_user_token import BitrixApiError

from settings import ilogger

if False:
    # for type annotations
    from typing import Optional, Sequence

    from .bitrix_user_token import BitrixUserToken
    from .bitrix_portal import BitrixPortal

from its_utils.functions.compatibility import get_null_boolean_field

NullBooleanField = get_null_boolean_field()

missing = object()


class _ListWithHash(list):
    # Костыль для ArrayField, который не будут чинить в Django<2.0
    def __hash__(self):
        return hash(tuple(self))


@six.python_2_unicode_compatible
class BitrixUser(models.Model):
    REFRESH_ERRORS = (
        (0, 'Нет ошибки'),
        (1, 'Не установлен портал (Wrong client)'),
        (2, 'Устарел ключ совсем (Expired token)'),
        (3, 'Инвалид грант (Invalid grant)'),
        (9, 'Надо разобраться (Unnown Error)'),
    )

    portal = models.ForeignKey('bitrix_auth.BitrixPortal', related_name='bitrix_user', on_delete=models.CASCADE)
    bitrix_id = models.IntegerField(blank=True, null=True)  # ID

    first_name = models.CharField(max_length=255, blank=True, default='')  # NAME
    last_name = models.CharField(max_length=255, blank=True, default='')  # LAST_NAME

    # Контакты
    email = models.CharField(max_length=255)
    work_phone = models.CharField(max_length=100, blank=True, default='')  # WORK_PHONE
    personal_mobile = models.CharField(max_length=100, blank=True, default='')  # PERSONAL_MOBILE
    # website = models.CharField(max_length=255, blank=True, default='')
    linkedin = models.CharField(max_length=255, blank=True, default='')  # UF_LINKEDIN
    facebook = models.CharField(max_length=255, blank=True, default='')  # UF_FACEBOOK
    twitter = models.CharField(max_length=255, blank=True, default='')  # UF_TWITTER
    skype = models.CharField(max_length=255, blank=True, default='')  # UF_SKYPE

    # ID групп, в которых состоит Битрикс-пользователь, через запятую
    groups = models.TextField(null=True, blank=True)
    groups_updated = models.DateTimeField(null=True, blank=True)
    # ID отделов, в которых состоит Битрикс-пользователь + их предки, через запятую
    departments = models.TextField(null=True, blank=True)
    departments_updated = models.DateTimeField(null=True, blank=True)
    # ID отделов, в которых состоит Битрикс-пользователь, через запятую, без родительских
    immediate_departments = models.TextField(null=True, blank=True)  # UF_DEPARTMENT
    immediate_departments_updated = models.DateTimeField(null=True, blank=True)
    # department = models.ForeignKey('bitrix_auth.BitrixDepartment', blank=True, null=True, on_delete=models.PROTECT)

    extranet = NullBooleanField(default=None, null=True)

    auth_token = models.CharField(max_length=32, null=True, blank=True)
    refresh_token = models.CharField(max_length=32, null=True, blank=True)
    auth_token_date = models.DateTimeField(null=True, blank=True)

    is_admin = models.BooleanField(blank=True, default=False)
    is_admin_updated = models.DateTimeField(blank=True, null=True)

    user_created = models.DateTimeField(null=True, default=timezone.now)

    user_is_active = models.BooleanField(default=True)  # ACTIVE
    refresh_error = models.PositiveSmallIntegerField(default=0, choices=REFRESH_ERRORS)

    application = models.ForeignKey('bitrix_auth.BitrixApp', null=True, on_delete=models.CASCADE)  # Это нафиг ненужно

    class Meta:
        app_label = 'bitrix_auth'
        unique_together = ('portal', 'bitrix_id')

    def save(self, *args, **kwargs):

        # Обновление токенов будем делать отдельным методом, чтобы кто-то случайно не перезатер
        # Возможно можно переделать используя update_fields
        if self.pk is not None:
            # fixme: похоже эти поля более не нужны и мы зря долбим БД?
            orig = BitrixUser.objects.get(pk=self.pk)
            self.auth_token = orig.auth_token
            self.refresh_token = orig.refresh_token
            self.auth_token_date = orig.auth_token_date

        return super(BitrixUser, self).save(*args, **kwargs)

    def update_from_bx_response(self, user, save=True):
        """Принимает словарь - данные пользователя от user.get/user.current
        и обновляет данные этого (self) пользователя
        """
        from .bitrix_department import BitrixDepartment

        if self.bitrix_id is None:
            self.bitrix_id = int(user['ID'])
        elif int(self.bitrix_id) != int(user['ID']):
            t = 'User mismatch: local #{self.bitrix_id} user_info#{info[ID]}'
            raise RuntimeError(t.format(self=self, info=user))

        def _f(field_name, default='', max_length=255):
            value = user.get(field_name) or default
            if max_length is not None:
                value = str(value)[:max_length]
            return value

        # Обновление основных полей
        self.first_name = _f('NAME')
        self.last_name = _f('LAST_NAME')
        self.email = _f('EMAIL')

        self.work_phone = _f('WORK_PHONE', max_length=100)
        self.personal_mobile = _f('PERSONAL_MOBILE', max_length=100)

        self.linkedin = _f('UF_LINKEDIN')
        self.facebook = _f('UF_FACEBOOK')
        self.twitter = _f('UF_TWITTER')
        self.skype = _f('UF_SKYPE')

        if 'UF_DEPARTMENT' in user: # hot fix для трагедии колапса скоупов 2022-03-16
            department_ids = user['UF_DEPARTMENT']
            if not(isinstance(department_ids, list)):
                department_ids = \
                    BitrixDepartment.normalize_uf_department(department_ids)
            self.immediate_department_ids = department_ids

        if save:
            self.save()

    @property
    def display_name(self):
        return u' '.join(filter(bool, (
            self.first_name.strip(),
            self.last_name.strip(),
        ))).strip() or self.email or u'Пользователь №{}'.format(self.bitrix_id)

    @property
    def short_display_name(self):
        first_name = self.first_name.strip()
        if first_name:
            return first_name
        return self.display_name

    @property
    def immediate_department_ids(self):
        dep_ids = (
            dep_id.strip() for dep_id in
            (self.immediate_departments or '').split(',')
        )
        return [int(dep_id) for dep_id in dep_ids if dep_id]

    @immediate_department_ids.setter
    def immediate_department_ids(self, immediate_department_ids):
        self.immediate_departments = ','.join(map(str, sorted(
            int(dep_id) for dep_id in immediate_department_ids
        )))
        self.extranet = self.immediate_department_ids == [] or \
                        self.immediate_department_ids == [0]
        self.immediate_departments_updated = timezone.now()

    @property
    def department_ids(self):
        dep_ids = (
            dep_id.strip() for dep_id in
            (self.departments or '').split(',')
        )
        return [int(dep_id) for dep_id in dep_ids if dep_id]

    @department_ids.setter
    def department_ids(self, department_ids):
        self.departments = ','.join(map(str, sorted(
            int(dep_id) for dep_id in department_ids
        )))
        self.extranet = self.department_ids == [] or \
                        self.department_ids == [0]
        self.departments_updated = timezone.now()

    @property
    def all_department_ids(self):
        return list(sorted(set(
            self.department_ids + self.immediate_department_ids,
        )))

    @all_department_ids.setter
    def all_department_ids(self, all_department_ids):
        self.department_ids = all_department_ids

    @property
    def group_ids(self):
        group_ids = (
            group_id.strip() for group_id in
            (self.groups or '').split(',')
        )
        return [int(group_id) for group_id in group_ids if group_id]

    @group_ids.setter
    def group_ids(self, group_ids):
        self.groups = ','.join(map(str, sorted(
            int(group_id) for group_id in group_ids
        )))
        self.groups_updated = timezone.now()

    def get_active_bitrix_user_token(self, application_names):
        # application_names = ['app1', 'app2]
        from bitrix_utils.bitrix_auth.models import BitrixUserToken
        for application_name in application_names:
            try:
                but = BitrixUserToken.objects.get(user=self, application__name=application_name, is_active=True)
                return but
            except BitrixUserToken.DoesNotExist:
                pass

        # Не найти токен можно по разным причинам поэтому и события в лог можно разные писать.
        # buts = BitrixUserToken.objects.filter(user=self) # все токены пользователя
        logtype = u"no_active_token"
        logdesc = u""
        for application_name in application_names:
            try:
                but = BitrixUserToken.objects.get(user=self, application__name=application_name)
                logtype += u"_{}_{}".format(application_name, but.refresh_error)
                logdesc += u" {} {}".format(application_name, but.get_refresh_error_display())
            except BitrixUserToken.DoesNotExist:
                logtype += u"_{}_notoken".format(application_name)
                logdesc += u" {} notoken".format(application_name)

        ilogger.warning(
                u"{}=>{} bx_user_id={} application_names={}".format(logtype, logdesc, self.id, application_names))
        raise BitrixUserToken.DoesNotExist()

    def get_bitrix_user_token(self, application_name):
        # Возможно когда-нибудь понадобится выбрать из нескольких приложений, тогда передавать может
        # application_name = ['app1', 'app2]
        from bitrix_utils.bitrix_auth.models import BitrixUserToken
        # NB! ТАК проверяем тип переменной на строку в коде, работающем на 2 И 3 питоне!
        if isinstance(application_name, six.string_types):
            but = BitrixUserToken.objects.get(user=self, application__name=application_name)
        else:
            but = BitrixUserToken.objects.filter(user=self, application__name__in=application_name).first()
            if but == None:
                # встретилась в вклидах такая ситуация, чето токены не пересоздались наверно
                # пришлось отработать, но вроде такого быть не должно
                but = BitrixUserToken(user=self,
                                      application=BitrixApp.objects.get(name=application_name[0]),
                                      auth_token_date=timezone.now())
                but.save()
        return but

    @classmethod
    def get_departments_from_bitrix(cls, departments, user_department_id=None):
        """
        Получить отделы, к которым принадлежит пользователь, т.е. записать текущий отдел и всех предков этого отдела
        user_department_id - id отделения, в котором состоит пользователь
        departments - JSON в том виде, что приходит из битрикса на запрос department.get
        """
        result = []
        departments = {each['ID']: each for each in departments}

        # Сначала найти в списке отделов тот, в котором находится пользователь
        # Потом найти всех его родителей
        log_messages = []
        for key, value in departments.items():
            if user_department_id == int(key):
                result.append(str(user_department_id))
                parent = departments.get(value.get('PARENT'))
                while parent:
                    log_messages.append(parent)
                    result.append(parent['ID'])
                    parent = departments.get(parent.get('PARENT'))
                return result

    def get_department_ids(self, bx_user_token, save=True):
        """Возвращает ID департаментов, в которых пользователь состоит.
        Всегда берет свежие данные из битрикса.
        (Только непосредственные отделы без предков по иерархии)

        :type bx_user_token: BitrixUserToken
        :param save: - Сохранить в записи пользователя новые ID отделов

        :rtype: list[int]

        :raises: BitrixApiError
        :raises: ValueError - if there's no user on portal
        """
        bx_id = self.bitrix_id

        try:
            user_info = self.portal.get_users(bx_user_token, bx_id=bx_id)[0]
        except IndexError:
            raise ValueError('No user with ID {} on portal'
                             .format(bx_id))
        department_ids = user_info['UF_DEPARTMENT']

        self.immediate_department_ids = department_ids
        if save:
            self.save(update_fields=[
                'extranet',
                'immediate_departments',
                'immediate_departments_updated',
            ])
        return self.immediate_department_ids

    def get_departments(self, bx_user_token, include_parents=False, save=True,
                        department_get_response=None):
        """Возвращает список отделов, в которых состоит пользователь.
        Всегда берет свежие данные из битрикса.

        :type bx_user_token: BitrixUserToken
        :param include_parents: Вернуть также родительские отделы
        :param save: - Сохранить в записи пользователя новые ID отделов

        :type department_get_response: list[dict]
        :param department_get_response: Ответ битрикса со списком ВСЕХ подразделений

        :rtype: list[dict]

        :raises: CallListException
        :raises: KeyError - если в переданном department_get_response отсутствует
        какое-либо из подразделений пользователя,
        например если получены только первые 50 подразделений
        """
        # ID отделов, в которых состоит пользователь
        own_department_ids = self.get_department_ids(bx_user_token, save=save)

        def _fmt_department(department):
            department_id = int(department['ID'])
            parent_id = department.get('PARENT')
            parent_id = int(parent_id) if parent_id else None
            return dict(
                id=department_id,
                name=department['NAME'],
                sort=int(department['SORT']),
                parent_id=parent_id,
                # is_immediate:
                # True, если пользователь непосредственно состоит в этом отделе.
                # False, если это родительский отдел одного из его отделов.
                is_immediate=department_id in own_department_ids,
            )

        params = None
        if not include_parents:
            # Только непосредственные отделы пользователя
            params = dict(ID=own_department_ids)
        if department_get_response is not None:
            departments = department_get_response
        else:
            # Иначе - получение всех отделов
            departments = bx_user_token.call_list_method_v2('department.get', params)


        # Словари {ID отдела: отдел}
        # Все отделы компании.
        departments_lookup = dict((int(dep['ID']), dep) for dep in departments)
        # Отделы в которых состоит пользователь (включая родительские)
        user_departments = dict()

        if not include_parents:
            # Отделы пользователя без родительских
            return [_fmt_department(departments_lookup[dep_id])
                    for dep_id in own_department_ids]

        def _add(department):
            # Добавить отдел и его родителей в отделы пользователя
            department_id = int(department['ID'])
            if department_id not in user_departments:
                parent_id = department.get('PARENT')
                parent_id = int(parent_id) if parent_id else None
                user_departments[department_id] = _fmt_department(department)
                if parent_id is not None:
                    _add(departments_lookup[parent_id])

        for department in departments:
            department_id = int(department['ID'])
            if department_id in own_department_ids:
                _add(department)
        departments_with_parents = list(user_departments.values())
        self.department_ids = [
            dep['id'] for dep in departments_with_parents
        ]
        if save:
            self.save(update_fields=[
                'departments',
                'departments_updated',
                'extranet',
            ])
        return departments_with_parents

    def get_groups(self, bx_user_token, save=True):
        """Возвращает группы, в которых состоит данный пользователь.
        Всегда берет свежие данные из битрикса.

        :type bx_user_token: BitrixUserToken
        :param save: Сохранить в записи пользователя новые ID групп

        :rtype: list[dict]

        :raises: CallListException
        """
        # Метод для получения груп отдает группы текущего пользователя
        assert bx_user_token.user_id == self.id
        groups = bx_user_token.call_list_method_v2('sonet_group.user.groups')

        groups = [dict(
            id=int(group['GROUP_ID']),
            name=group['GROUP_NAME'],
            # 'A' - владелец, 'E' - модератор, 'K' - пользователь
            user_role=group['ROLE'],
        ) for group in groups]
        self.group_ids = [group['id'] for group in groups]
        if save:
            self.save(update_fields=['groups', 'groups_updated'])
        return groups

    @staticmethod
    def _check_max_age(last_request_dt, max_age_secs):
        # True если не требуется повторить запрос, иначе False.
        if last_request_dt is None or max_age_secs is None:
            return False
        earliest_allowed_moment = \
            timezone.now() - datetime.timedelta(seconds=max_age_secs)
        return last_request_dt >= earliest_allowed_moment

    def get_access_records(self, bx_user_token=None, application_names=None,
                           max_age_secs=30*60,
                           save_groups_and_departments=True):
        """Возвращает список строк,
        если поле доступа (bitrix_utils.bitrix_auth.models.fields.BitrixAccessField)
        содержит любую из них, считается что пользователь имеет доступ.

        :type bx_user_token: BitrixUserToken

        :type application_names: list[str]
        :param application_names: список имен приложения (если не передан токен)

        :type max_age_secs: int
        :param max_age_secs: Время в секундах, сколько считать полученные
            от Б24 ID груп и отделов свежими и отдавать данные из нашей БД
            вместо запроса к Б24. По-умолчанию данные запрашиваются
            не чаще 1 раза за полчаса.
            Если передан None всегда берутся свежие данные из Б24.

        :param save_groups_and_departments: Сохранить полученные от Битрикс24
            данные о группах и отделах, в которых состоит пользователь.
            Акутально только если запрашиваются свежие данные из Б24.

        :rtype: list[str]
        :return: ['UA', 'U12', 'DR1', 'DR2', 'D2', 'SG42'] - такой ответ
            вернется для пользователя с битрикс-ID#12,
            состоящего в отделе#2 (подотделе отдела#1) и группе#42
            ['U666', 'SG42'] - для экстранетчика#666 в группе #42
        """
        dts = [
            self.departments_updated,
            self.groups_updated,
            self.immediate_departments_updated,
        ]
        if all(self._check_max_age(dt, max_age_secs) for dt in dts):
            return self.get_cached_access_records()
        else:
            # Если хотя бы один параметр просрочен (отделы или группы)
            # будут запрошены все параметры. Потенциально можно переделать,
            # чтобы обновлять группы и отделы индивидуально, если потребуется.
            return self.get_fresh_access_records(
                bx_user_token=bx_user_token,
                application_names=application_names,
                save_groups_and_departments=save_groups_and_departments,
            )

    def get_fresh_access_records(self, bx_user_token=None, application_names=None,
                                 save_groups_and_departments=True):
        """Возвращает список строк,
        если поле доступа (bitrix_utils.bitrix_auth.models.fields.BitrixAccessField)
        содержит любую из них, считается что пользователь имеет доступ.
        Всегда запрашивает свежие данные из битрикса.

        :type bx_user_token: BitrixUserToken

        :type application_names: list[str]
        :param application_names: список имен приложения (если не передан токен)

        :param save_groups_and_departments: Сохранить полученные от Битрикс24 данные
            о группах и отделах, в которых состоит пользователь.

        :rtype: list[str]
        :return: ['UA', 'U12', 'DR1', 'DR2', 'D2', 'SG42'] - такой ответ вернется
            для пользователя с битрикс-ID#12, состоящего в отделе#2 (подотделе отдела#1)
            и группе#42
            ['U666', 'SG42'] - для экстранетчика#666 в группе #42
        """
        if bx_user_token is None and application_names:
            bx_user_token = self.get_active_bitrix_user_token(application_names)
        if bx_user_token is None:
            raise ValueError('provide active bx_user_token or application_names')

        # Любое совпадение с этим списком дает пользователю доступ:
        # - Если открыт доступ всем пользователям (кроме экстранет)
        satisfying_access_records = _ListWithHash(
            [] if self.extranet else ['UA']
        )

        satisfying_access_records.append(
            # - Если открыт доступ нашему пользователю
            'U{}'.format(self.bitrix_id),
        )

        satisfying_access_records.extend([
            # - Если дан доступ любой из групп пользователя
            'SG{}'.format(group['id'])
            for group in self.get_groups(bx_user_token, save=save_groups_and_departments)
        ])

        if self.extranet:
            return satisfying_access_records

        departments = self.get_departments(bx_user_token, include_parents=True,
                                           save=save_groups_and_departments)
        for department in departments:
            # - Если дан рекурсивный доступ любому отделу пользователя
            # (непосредственному отделу или родительскому отделу)
            satisfying_access_records.append('DR{}'.format(department['id']))
            # - Если дан нерекурсивный доступ непосредственному отделу пользователя
            if department['is_immediate']:
                satisfying_access_records.append('D{}'.format(department['id']))

        return satisfying_access_records

    def get_cached_access_records(self):
        """Аналогично ``get_fresh_access_records``, но без обращения к Б24.
        NB! Потенциально устаревшие значения.

        :rtype: list[str]
        :return: ['UA', 'U12', 'DR1', 'DR2', 'D2', 'SG42'] -
            такой ответ вернется для пользователя с битрикс-ID#12,
            состоящего в отделе#2 (подотделе отдела#1) и группе#42
            ['U666', 'SG42'] - для экстранетчика#666 в группе #42
        """

        ua = ['UA']
        u = ['U%s' % self.bitrix_id]
        sg = ['SG%s' % id_ for id_ in self.group_ids]
        d = ['D%s' % id_ for id_ in self.immediate_department_ids]
        dr = ['DR%s' % id_ for id_ in self.all_department_ids]

        if self.extranet:
            return _ListWithHash(u + sg)
        return _ListWithHash(ua + u + sg + d + dr)

    def get_groups_and_departments(self, app_name=None):
        """
        Если прошел час с получения токена, обновляет информацию о портале и берет информацию из БД
        Возвращает список id отделов и список id групп
        В битриксе отдел у пользователя передается в виде массива.
        Либо раньше он мог состоять в нескольких, либо они собираются это сделать, что вряд ли.
        В общем, на это надо обратить внимание.
        """

        if app_name:
            bx_token = self.get_bitrix_user_token(app_name)

        else:
            from bitrix_utils.bitrix_auth.models import BitrixUserToken
            bx_token = BitrixUserToken.objects.filter(user=self).first()

        if False:  # Не будем обновлять до выхода из приложения
            if (timezone.now() - self.auth_token_date).total_seconds() >= 3600:
                response = batch_api_call(
                    domain=self.portal.domain,
                    auth_token=None,
                    methods=[{'user.current': None},
                             {'department.get': None},
                             {'sonet_group.user.groups': None}, ],
                    bitrix_user_token=bx_token
                )

                user_info = response[0]['result']['result']['data_0']
                departments = response[0]['result']['result'].get('data_1')
                groups = [each['GROUP_ID'] for each in response[0]['result']['result'].get('data_2', [])]

                update_fields = []

                # В result_next может и массив прийти, если он пустой
                if isinstance(response[0]['result']['result_next'], dict):
                    # Если загрузили не все отделы, получаем остальные
                    next_depts = response[0]['result']['result_next'].get('data_1')
                    if next_depts:
                        rest_depts = bx_token.call_list_method_v2('department.get', {
                            'start': next_depts
                        })
                        if rest_depts:
                            departments.extend(rest_depts)

                    # Если загрузили не все группы, получаем остальные
                    next_groups = response[0]['result']['result_next'].get('data_2')
                    if next_groups:
                        rest_groups = bx_token.call_list_method_v2('sonet_group.user.groups', {
                            'start': next_groups
                        })
                        if rest_groups:
                            groups.extend([each['GROUP_ID'] for each in rest_groups])

                if departments:
                    departments = self.get_departments_from_bitrix(departments, user_info['UF_DEPARTMENT'][0])
                    try:
                        self.departments = ','.join(departments)
                        self.departments_updated = timezone.now()
                        update_fields += ['departments', 'departments_updated']
                    except TypeError:
                        ilogger.exception('{}, {}'.format(response, departments))
                else:
                    departments = []

                self.groups = ','.join(groups)
                self.groups_updated = timezone.now()
                update_fields += ['groups', 'groups_updated']
                self.save(update_fields=update_fields)
                return groups, departments

        # groups и departments могут быть равны None
        try:
            groups = list(filter(bool, self.groups.split(',')))
        except AttributeError:
            groups = []

        try:
            departments = list(filter(bool, self.departments.split(',')))
        except AttributeError:
            departments = []

        return groups, departments

    def __str__(self):
        return u'#{self.id} {self.display_name} {self.portal}'.format(self=self).strip()

    @classmethod
    def user_names(cls, token, user_bitrix_ids, db_filter=missing):
        """Возвращает имена пользователей на портале по их id,
        если пользователь есть в нашей БД, возьмет из БД,
        иначе от user.get битрикса

        :type token: BitrixUserToken
        :param token: NB! чтобы работало с экстранетчиками,
            токен должен быть экстранетный/админский

        :type user_bitrix_ids: list[int]
        :param user_bitrix_ids: Б24-id пользователей на портале

        :type db_filter: dict
        :param db_filter: по умолч. dict(user_is_active=True)

        :rtype: dict[int, str]
        :return: {42: 'Вася Пупкин', 1: 'Админ Админов'}, где
            ключи - Б24-id пользователей,
            значения - имена пользователей;
            NB! если пользователя нет ни в БД ни в битриксе,
            запись о нем будет отсутствовать в словаре
        """
        if not user_bitrix_ids:
            return {}

        portal = token.user.portal
        user_bitrix_ids = list(set(map(int, user_bitrix_ids)))

        if db_filter is missing:
            db_filter = dict(user_is_active=True)
        db_filter = models.Q(**db_filter) if isinstance(db_filter, dict) \
            else db_filter

        db_users = cls.objects \
            .only('id', 'bitrix_id', 'first_name', 'last_name', 'email') \
            .filter(portal=portal, bitrix_id__in=user_bitrix_ids) \
            .filter(db_filter)

        res = dict((u.bitrix_id, u.display_name)
                   for u in db_users)

        if len(res) == len(user_bitrix_ids):
            # Все пользователи есть в БД
            return res

        missing_user_ids = set((uid for uid in user_bitrix_ids
                                if uid not in res))
        bx_users = portal.get_users(token, bx_id=missing_user_ids)

        for user in bx_users:
            uid = int(user['ID'])
            assert uid in missing_user_ids
            res[uid] = cls(
                bitrix_id=uid,
                first_name=user['NAME'] or '',
                last_name=user['LAST_NAME'] or '',
                email=user.get('EMAIL') or '',
            ).display_name

        return res

    @staticmethod
    def exclude_chatbots(token, bx_portal, users, **kwargs):
        """Исключает чатботов из списка пользователей.
        Для облачного портала, ничего не делает, т.к. облачный
        user.get не отдает чатботов. Для коробки убирает
        пользователей из подраздаления "чатботы"/"чат-боты"

        NB! нормализует UF_DEPARTMENT пользователей, приводя к списку

        fixme - есть альернативный, менее костыльный способ проверки
            на чатоботов через imbot.bot.list:
            https://dev.1c-bitrix.ru/learning/course/index.php?COURSE_ID=93&LESSON_ID=7873#imbot_bot_list
            Главный минус - необходимость REST-разрешения imbot
            TODO: проверить совпадение ID пользователей-чатботов
                на коробочном user.get и ботов из imbot.bot.list


        :type token: BitrixUserToken
        :type bx_portal: BitrixPortal

        :type users: list[dict]
        :param users: список пользователей, результат user.get

        :param kwargs: kwargs для BitrixPortal.get_department_tree

        :rtype: list[dict]
        :return: список пользователей без чатботов
        """
        from .bitrix_department import BitrixDepartment

        BitrixDepartment.normalize_uf_departments(users)

        if not bx_portal.is_box(token=token):
            return users

        chatbot_departments = BitrixDepartment.get_chatbot_departments(
            token=token,
            bx_portal=bx_portal,
            **kwargs
        )
        chatbot_dep_ids = [dep['id'] for dep in chatbot_departments]

        def is_bot(u):
            return any(int(dep_id) in chatbot_dep_ids
                       for dep_id in u['UF_DEPARTMENT'])

        return [user for user in users if not is_bot(user)]

    def send_notification(self, application_name, message):
        bxapp = BitrixApp.objects.get(name=application_name)
        from bitrix_utils.bitrix_auth.models import BitrixNotification
        return BitrixNotification(user=self, application=bxapp, type=0, message=message).save()

    def im_notify(
            self, to, message, type='SYSTEM',
            bx_user_token=None, application_names=None,
    ):
        # type: (int, str, str, Optional[BitrixUserToken], Optional[Sequence[str]]) -> dict
        """Отправить уведомление от токена пользователя,
        см. https://dev.1c-bitrix.ru/rest_help/im/im_notify.php
        """
        from .bitrix_user_token import BitrixUserToken

        if not application_names and not bx_user_token:
            raise AttributeError('application_names or bx_user_token required')
        if application_names and bx_user_token:
            raise AttributeError(
                'provide application_names or bx_user_token, not both')

        if bx_user_token is None:
            bx_user_token = self.get_active_bitrix_user_token(
                application_names=application_names)
            if bx_user_token is None:
                raise BitrixUserToken.DoesNotExist
        else:
            assert bx_user_token.user_id == self.id, 'user and token mismatch'

        return bx_user_token.call_api_method('im.notify', dict(
            to=to,
            message=message,
            type=type,
        ))

    def update_is_admin(self, bx_user_token, save=True,
                        throttle=datetime.timedelta(minutes=2)):
        # type: (BitrixUserToken, bool, Optional[datetime.timedelta]) -> None
        """Узнать от битрикса админ ли пользователь,
        установить поле is_admin у пользователя.

        :param bx_user_token: токен пользователя
        :param save: сохранить в БД
        :param throttle: максимальная частота отправки запроса
            проверки админства к битриксу.

        Usage:
            >>> f = dict(is_active=True, user__user_is_active=True, user__is_admin=False)
            >>> token = BitrixUserToken.objects.filter(**f).first()
            >>> token.user.update_is_admin(token)  # Первый раз запрос к Битриксу выполняется
            >>> token.user.update_is_admin(token)  # Повторный запрос не выполняется, т.к. throttle=(2 минуты)
            >>> token.user.update_is_admin(token, throttle=None)  # Запрос принудительно выполняется
            >>> token.user.is_admin  # Если пользователь не стал админом - по прежнему False
            False
        """
        assert bx_user_token.user_id == self.id, 'token mismatch'

        # throttle-проверка
        now = timezone.now()
        if (
                self.is_admin is not None and
                throttle is not None and
                self.is_admin_updated is not None and
                self.is_admin_updated >= (now - throttle)
        ):
            return

        is_admin = self.is_admin
        try:
            is_admin = bx_user_token.call_api_method('user.admin')['result']
        except BitrixApiError as e:
            if e.status_code not in [500, 502]:
                #is_admin = False
                ilogger.info('portal_return_gte500', "{}".format(get_admin_a_tag(self)))
                pass
        if not isinstance(is_admin, bool):
            raise ValueError('user.admin did not return bool: {!r}'
                             .format(is_admin))

        self.is_admin = is_admin
        self.is_admin_updated = timezone.now()

        if save:
            self.save(update_fields=['is_admin', 'is_admin_updated'])
