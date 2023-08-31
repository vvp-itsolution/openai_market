# -*- coding: utf-8 -*-
import re
from six import iteritems
from six.moves import reduce
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.db import transaction


valid_access_record_re = re.compile(r'^UA|(?:(?:U|DR?|SG)\d+)$')


def flatten(matrix):
    # flatten:: A:Iter+Index, B:Iter+Concat => A[B[x]] -> B[x]
    # flatten([(1, 2, 3), (4, 5, 6)]) == (1, 2, 3, 4, 5, 6)
    # flatten(([1, 2, 3], [4, 5, 6])) == [1, 2, 3, 4, 5, 6]
    # flatten(()) == ()
    # flatten([]) == []
    empty_value = type(matrix[0] if matrix else matrix)()
    return reduce(lambda acc, item: acc + item, matrix, empty_value)


def intersection_all(*collections):
    # intersection_all([1, 2, 3, 4], [2, 3, 4, 5], [3, 4, 5, 6]) == set([3, 4])
    collections = list(filter(bool, collections))
    if not collections:
        return set()
    res = set(collections[0])
    for collection in collections[1:]:
        res &= set(collection)
    return res


class AccessArray(list):
    def __init__(self, *args, **kwargs):
        lst = list(sorted(rec.upper() for rec in list(*args, **kwargs)))
        for rec in lst:
            if not valid_access_record_re.match(rec):
                raise ValueError('Invalid access record: %r' % rec)
        super(AccessArray, self).__init__(lst)

    def __repr__(self):
        return '{cls}({super})'.format(
            cls=self.__class__.__name__,
            super=super(AccessArray, self).__repr__(),
        )

    def intersects(self, access_records):
        return any(rec in self for rec in access_records)

    def grouped_dict(self):
        """Группирует записи по типу.

        :rtype: dict
        :return: Пример возвращаемого занчения:
            {
                'users': [42],
                'groups': [5],
                'departments': [
                    {'id': 4, 'recursive': True},
                    {'id': 2, 'recursive': False},
                ],
                'all_users': False,
            }
            Для AccessArray(['U42', 'DR4', 'D2', 'SG5'])
        """
        grouped = dict(
            users=[],
            groups=[],
            departments=[],
            all_users=False,
        )
        for rec in self:
            rec = rec.upper()
            if rec == 'UA':
                grouped['all_users'] = True
            elif rec.startswith('U'):
                _, uid = rec.split('U', 1)
                grouped['users'].append(int(uid))
            elif rec.startswith('SG'):
                _, gid = rec.split('SG', 1)
                grouped['groups'].append(int(gid))
            elif rec.startswith('DR'):
                _, dep_id = rec.split('DR', 1)
                grouped['departments'].append(dict(
                    id=int(dep_id),
                    recursive=True,
                ))
            elif rec.startswith('D'):
                _, dep_id = rec.split('D', 1)
                grouped['departments'].append(dict(
                    id=int(dep_id),
                    recursive=False,
                ))
            else:
                raise ValueError('Invalid access record: %r' % rec)
        return grouped

    @classmethod
    def from_grouped_dict(cls, grouped_dict):
        """Обратный метод для grouped_dict.

        :type grouped_dict: dict
        :param grouped_dict: см. AccessArray.grouped_dict
        :rtype: AccessArray
        :return: пример: AccessArray(['U42', 'DR4', 'D2', 'SG5'])
        """
        res = []
        if grouped_dict['all_users']:
            res.append('UA')
        for uid in grouped_dict['users']:
            res.append('U%d' % uid)
        for gid in grouped_dict['groups']:
            res.append('SG%d' % gid)
        for dep in grouped_dict['departments']:
            res.append('{prefix}{id}'.format(
                prefix='DR' if dep['recursive'] else 'D',
                id=dep['id'],
            ))
        return cls(res)

    @classmethod
    def normalize_read_edit_access(cls, read_access, edit_access):
        """Нормализация прав доступа чтения+редактирования:
        - удаляет невалидные записи или кидает ошибку
        - удаляет дубли
        - добавляет недостающие права:
            - при добавлении права редактирования добавляет аналогичное право чтения
        - убирает избыточные права:
            - если дан рекурсивный доступ отделу, убирает избыточный нерекурсивный
        - сортирует по-алфавиту

        TODO: Учитывать при нормализации автора статьи

        :type read_access: Iterable[str]
        :type edit_access: Iterable[str]
        :rtype: tuple[AccessArray, AccessArray]
        :return: (normalized_read_access, normalized_edit_access)
        """
        new_read_access = set(cls(read_access))
        new_edit_access = set(cls(edit_access))

        # Добавляет права чтения на имеющиеся права редактирования
        for edit_access_record in new_edit_access:
            new_read_access.add(edit_access_record)

        # Убираем избыточные D{N} права при имеющемся DR{N} праве
        dr_read_records = {rec for rec in new_read_access if rec.startswith('DR')}
        dr_edit_records = {rec for rec in new_edit_access if rec.startswith('DR')}
        for access, dr_records in [
            [new_read_access, dr_read_records],
            [new_edit_access, dr_edit_records],
        ]:
            for dr_record in dr_records:
                access.discard(dr_record.replace('R', ''))

        return cls(new_read_access), cls(new_edit_access)

    def normalized(self):
        return self.normalize_read_edit_access(self, self)[0]

    def departments_intersection(self):
        """Для ненормализованного списка прав возвращает
        наиболее частные права для отделов (= предпочтительно нерекурсивные):
        AccessArray([
            'UA', 'UA', 'U1', 'SG1',  # <- Подобные права всегда игнорируются
            'D1', 'DR2', 'D2', 'DR3',  # <- В результат попадет наиболее
                                       # частное право для каждого отдела
        ]).departments_intersection() == AccessArray(['D1', 'D2', 'DR3'])

        :rtype: AccessArray
        """
        id_to_recursive = {}
        for rec in self:
            if not rec.startswith('D'):
                continue
            id_ = int(rec.lstrip('DR'))
            recursive = rec.startswith('DR')
            id_to_recursive.setdefault(id_, recursive)
            if not recursive:
                id_to_recursive[id_] = False
        return AccessArray([
            'D{}{}'.format('R' if recursive else '', id_)
            for id_, recursive in iteritems(id_to_recursive)
        ])

    def concrete_user_ids(self, admin_token, parent_access_arrays=None,
                          max_data_age=1*60*60):
        """Возвращает последовательность id пользователей,
        которые попадают в данный список прав.
        NB! Дорогой метод, т.к. может включать запросы к API Б24

        :type admin_token: BitrixUserToken
        :param admin_token: админский токен,
            для проверки вхождения в группы

        :type parent_access_arrays: Iterable[AccessArray]
        :param parent_access_arrays: Права доступа чтения
            к родительским разделам. Требуются, т.к. при невозможности
            чтения любого из родителей, нет доступа и ко всем потомкам.

        :param max_data_age: макс. время прошлого запроса членов
            групп и отделов (в секундах)

        :rtype: set[Union[int, str]]
        :returns:
            {'UA'} - доступно всем сотрудникам
            {'UA', 42} - доступно всем сотрудникам + Экстранетчику#42
            {1, 2, 42} - доступно пользователям #1, #2 и #42
        """
        from ...models import BitrixDepartment, BitrixGroup

        if parent_access_arrays is None:
            parent_access_details = []
        else:
            parent_access_details = [AccessArray(arr).grouped_dict()
                                     for arr in parent_access_arrays]
        detailed = self.grouped_dict()

        # Только при отсутствии в списке прав UA возвращаем:
        # - записи отделов
        # - записи интранет-групп
        # - записи сотрудников
        # Т.к. все эти записи покрываются правилом UA (все сотрудники)
        ua = detailed['all_users'] and all(d['all_users']
                                           for d in parent_access_details)
        get_group_ids = set(
            detailed['groups'] +
            flatten([details['groups'] for details in parent_access_details])
        )
        groups = []
        for group_id in get_group_ids:
            try:
                group, _, _ = BitrixGroup.from_bitrix_id(admin_token, group_id)
            except BitrixGroup.NoneOnPortal:
                continue
            if not ua or group.extranet:
                groups.append(group)

        group_member_ids = dict(
            (group.bitrix_id, [m['id'] for m in group.get_members(admin_token)])
            for group in groups
        )

        department_user_ids = {}
        if not ua:
            departments_intersection = AccessArray.from_grouped_dict(dict(
                users=[],
                groups=[],
                all_users=False,
                departments=flatten([details['departments'] for details in
                                     [detailed] + parent_access_details])
            )).departments_intersection().grouped_dict()['departments']

            db_departments = dict(
                (dep.bitrix_id,  dep) for dep in
                BitrixDepartment.objects.filter(
                    portal_id=admin_token.user.portal_id,
                    bitrix_id__in=[dep['id'] for dep in
                                   departments_intersection],
                )
            )

            def get_department(bitrix_id):
                return db_departments.get(bitrix_id) or BitrixDepartment(
                    bitrix_id=bitrix_id,
                    portal_id=admin_token.user.portal_id,
                )
            for department in departments_intersection:
                id_ = department['id']
                department_user_ids[id_] = [
                    u['bitrix_id'] for u in get_department(id_).get_users(
                        admin_token=admin_token,
                        recursive=department['recursive'],
                        max_age_sec=max_data_age,
                    )
                ]

        def all_user_ids(details):
            group_members = flatten([group_member_ids.get(group_id, [])
                                     for group_id in details['groups']])
            department_users = flatten([
                department_user_ids.get(dep['id'], [])
                for dep in details['departments']
            ])
            return details['users'] + group_members + department_users

        # Исключаем интранетчиков
        exclude_user_ids = set()
        if ua:
            portal = admin_token.user.portal
            intranet_users = portal.get_users(admin_token, active=None)
            exclude_user_ids = set(int(u['ID']) for u in intranet_users)

        access_layers = [
            all_user_ids(details) for details in
            [detailed] + parent_access_details
        ]
        user_ids = set(
            uid for uid in intersection_all(*access_layers)
            if uid not in exclude_user_ids
        )
        if ua:
            user_ids.add('UA')
        return user_ids


class BitrixAccessField(ArrayField):
    """Поле с битриксоподобными правами доступа,
    может быть использовано для того, чтобы:
    1) Продублировать в своей базе права объекта из Б24.
    2) Настроить права доступа к чему-либо по сотрудникам, группам, разделам.
    Пример использования:
    class Smth(models.Model):
        read_access = BitrixAccessField(default=lambda: ['UA'])
        edit_access = BitrixAccessField(default=list)
    Значения:
        UA - доступ для всех
        U42 - доступ для пользователя с Битрикс-id 42
        D666 - Доступ для пользователей в отделе #666
        DR666 - Доступ для пользователей в отделе #666 и подотделах отдела #666
        SG15 - Доступ для пользователей из группы #15
    Пример прав доступа в доках Б24:
    https://dev.1c-bitrix.ru/rest_help/log/log_blogpost_add.php

    todo: валидация записываемых значений
    """
    description = 'Bitrix access field'

    def __init__(self, **kwargs):
        super(BitrixAccessField, self).__init__(
            base_field=models.CharField(max_length=32),
            size=None,
            **kwargs
        )

    def deconstruct(self):
        name, path, args, kwargs = super(BitrixAccessField, self).deconstruct()
        del kwargs['base_field']
        del kwargs['size']
        return name, path, args, kwargs

    def to_python(self, value):
        if isinstance(value, AccessArray) or value is None:
            return value

        return AccessArray(value)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return AccessArray(value)

    def accessible_by_user(self, bx_user, bx_user_token=None, application_names=None, qs=None):
        """Проверка наличия у Битрикс-пользователя прав доступа,
        с учетом его групп и подразделений.

        Usage:

            class MyModel(models.Model):
                access_field = BitrixAccessField()

            available_records = MyModel._meta.get_field('access_field') \
                .accessible_by_user(bx_user, bx_user_token)

        :type bx_user: bitrix_utils.bitrix_auth.models.BitrixUser
        :type bx_user_token: bitrix_utils.bitrix_auth.models.BitrixToken
        :type application_names: list[str]
        :param application_names: список имен приложения для получения активного токена
        (нужно только если не передан bx_user_token)
        :type qs: django.db.models.query.QuerySet
        :rtype: django.db.models.query.QuerySet
        :raises: bitrix_utils.bitrix_auth.functions.call_list_method.CallListException
        """
        if qs is None:
            qs = self.model.objects.all()
        access_records = bx_user.get_access_records(bx_user_token=bx_user_token,
                                                    application_names=application_names)
        return qs.filter(**{
            '{}__overlap'.format(self.name): access_records,
        })
