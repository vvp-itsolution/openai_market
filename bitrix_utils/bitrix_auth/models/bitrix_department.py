# -*- coding: UTF-8 -*-
from six import (
    itervalues, viewkeys, iteritems,
    python_2_unicode_compatible,
    string_types, integer_types,
)
from django.contrib.postgres.fields import ArrayField
from django.core.cache import cache
from django.db import models, transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from mptt.models import MPTTModel, TreeForeignKey

from ..functions.first import first
from .bitrix_user import BitrixUser


if False:
    # for type annotations
    from django.db.models import QuerySet

    from .bitrix_portal import BitrixPortal
    from .bitrix_user_token import BitrixUserToken


def _sort_by_sort(lst):
    return sorted(
        lst,
        key=lambda o: o['sort'] if o['sort'] is not None else float('-inf')
    )


_missing = object()


@python_2_unicode_compatible
class BitrixDepartment(MPTTModel):
    """Отдел/подразделение компании
    """
    USERS_CACHE_KEY_TEMPLATE = 'departments-users-updated' \
                               '-p#{self.portal_id}-bx#{self.bitrix_id}'
    CHATBOT_DEPARTMENTS = 'чвтботы', 'чат-боты',

    bitrix_id = models.IntegerField()
    portal = models.ForeignKey('bitrix_auth.BitrixPortal', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    head_id = models.IntegerField(null=True, blank=True)
    sort = models.IntegerField(null=True, blank=True)
    parent = TreeForeignKey('self',
                            null=True,
                            blank=True,
                            related_name='children',
                            db_index=True,
                            on_delete=models.CASCADE)

    users = ArrayField(models.IntegerField(null=False), null=True)

    class Meta:
        app_label = 'bitrix_auth'

    def __str__(self):
        return u'%s "%s"' % (self.portal, self.name)

    @staticmethod
    def normalize_uf_department(value):
        """Приводит UF_DEPARTMENT пользователя к списку id подразделений
        """
        if isinstance(value, string_types):
            if ',' in value:
                pieces = value.split(',')
            elif ';' in value:
                pieces = value.split(';')
            else:
                pieces = [value]
            return list(sorted(set(
                int(id_.strip()) for id_ in pieces if id_.strip()
            )))
        if isinstance(value, integer_types):
            return [value]
        if isinstance(value, list):
            return list(sorted(set(
                int(v) for v in value
            )))
        if not value:
            return []
        raise ValueError('invalid UF_DEPARTMENT: %r' % value)

    @classmethod
    def normalize_uf_departments(cls, users):
        """Нормализует UF_DEPARTMENT у каждого пользователя
        NB! inplace mutation

        :type users: list[dict]
        """
        for user in users:
            user['UF_DEPARTMENT'] = \
                cls.normalize_uf_department(user.get('UF_DEPARTMENT'))
        return users

    def dict(self, **kwargs):
        return dict(
            id=self.bitrix_id,
            name=self.name,
            parent_id=self.parent.bitrix_id if self.parent else None,
            head_id=self.head_id,
            sort=self.sort,
            **kwargs
        )

    @classmethod
    def portal_roots(cls, portal_id):
        """Возвращает корневые раздел по данным нашей БД

        :param portal_id: id портала у нас
        :rtype: QuerySet[BitrixDepartment]
        """
        return cls.objects.filter(parent=None, portal_id=portal_id)

    @property
    def is_portal_root(self):
        return self.parent_id is None

    def tree(self):
        """Возвращает подерево отделов на основании наших данных в БД,
        корнем поддерева выступает текущий отдел, для получения
        всего дерева метод надо вызвать у корневого отдела портала

        NB! Информация может быть заметно устаревшей!
        Для получения более актуальных данных см. BitrixPortal.get_department_tree

        :rtype: dict
        Returns:
            {
                'id': 42,
                'name': 'Бухгалтерия',
                'sort': 500,
                'head_id': 12,  # Битриксовый ID главы отдела или None
                'parent_id': 1,
                'children': [
                    {
                        'id': 43,
                        'name': '1С-Бухгалтерия',
                        'sort': 500,
                        'head_id': None,  # Битриксовый ID главы отдела или None
                        'parent_id': 42,
                        'children': [],
                    },
                ],
            }
        """
        departments = dict(
            (department.bitrix_id, department.dict(children=[]))
            for department in
            self.get_descendants(include_self=True).select_related('parent')
        )
        for department in _sort_by_sort(itervalues(departments)):
            if department['id'] == self.bitrix_id or \
                    department['parent_id'] is None:
                continue
            parent = departments[department['parent_id']]
            parent['children'].append(department)
        return departments[self.bitrix_id]

    def get_fresh_users(self, admin_token, save=None,
                        recursive=False, max_tree_age_sec=30*60, **filter_):
        """Возвращает свежие данные о пользователях в подразделении
        NB! Важный момент, не возвращает глав подразделений,
        если они не состоят в данном подразделении,
        что может быть хорошо или плохо в контексте конкретной задачи

        :type admin_token: BitrixUserToken
        :param save: Сохранить изменения в БД? По умолч. сохраняет
        если ничего не передано в filter_
        :param recursive: вернуть также пользователей в подотделах
        :param max_tree_age_sec: (только при переданном параметре recursive)
            сколько времени считать иерархию отделов актуальной (в сек-х)
        :param filter_: доп. параметры выборки
        :rtype: list[dict]
        Returns:
            [{
                bitrix_id: 42,  # есть у каждого элемента
                local_id: 666,  # есть у логинившихся
                bitrix_response: <данные пользователя из user.get>,
            }]
        """
        assert self.portal_id == admin_token.user.portal_id

        sub_department_ids = []
        if recursive:
            tree = self.portal.get_department_tree(
                admin_token,
                max_age_sec=max_tree_age_sec,
            )
            tree = self._find_department_in_tree(self.bitrix_id, tree)
            if tree is None:
                raise RuntimeError('the department is absent from'
                                   ' the new tree, perhaps it was deleted?')

            def _add_sub(sub_department):
                sub_department_ids.append(sub_department['id'])
                for child in sub_department['children']:
                    _add_sub(child)
            for sub_department in tree['children']:
                _add_sub(sub_department)

        filter_by = dict(
            UF_DEPARTMENT=[self.bitrix_id] + sub_department_ids,
            **filter_
        )
        if save is None:
            save = not filter_
        users = self.portal.get_users(
            token=admin_token,
            policy='soft-exclude',
            bx_filter=filter_by,
        )

        local_user_ids = dict(
            (user['bitrix_id'], user['id'])
            for user in BitrixUser.objects
            .filter(portal_id=self.portal_id,
                    bitrix_id__in=[int(u['ID']) for u in users])
            .values('id', 'bitrix_id')
        )
        res = [dict(
            bitrix_id=int(user['ID']),
            local_id=local_user_ids.get(int(user['ID'])),
            bitrix_response=user,
        ) for user in users]

        self.users = [
            user['bitrix_id'] for user in res
            if self.bitrix_id in user['bitrix_response']['UF_DEPARTMENT']
        ]
        if not save:
            return res

        if recursive:
            dep_id_to_new_users = dict((dep_id, [])
                                       for dep_id in sub_department_ids)
            dep_id_to_new_users[self.bitrix_id] = []
            for user in res:
                for dep_id in user['bitrix_response']['UF_DEPARTMENT']:
                    if dep_id not in dep_id_to_new_users:
                        continue
                    dep_id_to_new_users[dep_id].append(user['bitrix_id'])
            for bitrix_dep_id, user_ids in iteritems(dep_id_to_new_users):
                BitrixDepartment.objects.filter(
                    portal_id=self.portal_id,
                    bitrix_id=bitrix_dep_id,
                ).update(users=user_ids)
                BitrixDepartment(
                    portal_id=self.portal_id,
                    bitrix_id=bitrix_dep_id,
                )._set_users_updated()
        else:
            self.save()
            self._set_users_updated()
        return res

    def get_cached_users(self):
        """Возвращает сохраненных в нашей БД пользователей в подразделении
        NB! Только непосредственные пользователи в отделе,
        если глава подразделения не состоит в этом отделе,
        он также будет отсутствовать в списке
        NB! Данные могут быть заметно устаревшими, см. get_users

        :rtype: list[dict]
        Returns:
            [{
                bitrix_id: 42,  # есть у каждого пользователя
                local_id: 666,  # у логинившихся в приложение
                bitrix_response: None,  # всегда None
            }]
        """
        user_ids = self.users
        if user_ids is None:
            return None
        local_user_ids = dict(
            (user['bitrix_id'], user['id'])
            for user in BitrixUser.objects
            .filter(portal_id=self.portal_id, bitrix_id__in=user_ids)
            .values('id', 'bitrix_id')
        )
        return [dict(
            bitrix_id=user_id,
            local_id=local_user_ids.get(user_id),
            bitrix_response=None,
        ) for user_id in user_ids]

    @property
    def _cache_users_key(self):
        return self.USERS_CACHE_KEY_TEMPLATE.format(self=self)

    def _get_users_updated(self):
        return cache.get(self._cache_users_key)

    def _set_users_updated(self, when=None, expires=None):
        if when is None:
            when = timezone.now()
        return cache.set(self._cache_users_key, when, expires)

    def get_users(self, admin_token, recursive=False, max_age_sec=30*60,
                  max_tree_age_sec=_missing, admin_mode=False, save=True):
        """Возвращает пользователей в подразделении
        NB! Главы отделов не считаются членами этих отделов,
        если не состоят в них

        :type admin_token: BitrixUserToken
        :param recursive: включить пользователей в подотделах?
        :param max_age_sec: сколько секунд брать пользователей из нашей БД
        :param max_tree_age_sec: сколько секунд брать иерархию из нашей БД
        (только для рекурс. запросов, по умолч. == max_age_sec)
        :param admin_mode: ADMIN_MODE для user.get
        :param save: сохранить свежие данные в БД?
        :rtype: list[dict]
        Returns:
            [{
                bitrix_id: 42,  # есть у каждого элемента
                local_id: 666,  # есть у логинившихся
                bitrix_response: <данные пользователя из user.get> or None,
            }]
        """
        if max_age_sec is not None:
            last_update = self._get_users_updated()
            if last_update is not None and \
                    (timezone.now() - last_update).seconds <= max_age_sec:
                immediate_users = self.get_cached_users()
                if not recursive and immediate_users is not None:
                    return immediate_users
                if immediate_users is not None:
                    recursive_users = []
                    for child in self.get_children().select_related('portal'):
                        recursive_users.extend(child.get_users(
                            admin_token=admin_token,
                            recursive=True,
                            max_age_sec=max_age_sec,
                            max_tree_age_sec=max_tree_age_sec,
                            admin_mode=admin_mode,
                        ))
                    # concat and rm duplicates
                    return list(itervalues(dict(
                        (user['bitrix_id'], user)
                        for user in (immediate_users + recursive_users)
                    )))

        if max_tree_age_sec is _missing:
            max_tree_age_sec = max_age_sec
        return self.get_fresh_users(admin_token, save=save, recursive=recursive,
                                    admin_mode=admin_mode,
                                    max_tree_age_sec=max_tree_age_sec)

    @classmethod
    @method_decorator(transaction.atomic)
    def update_from_tree(cls, portal_id, tree, delete_missing=True):
        """Обновляет отделы, чтобы соответствовали дереву подразделений
        на Б24-портале

        :param portal_id: внутренний id портала
        :param tree: см. BitrixPortal.get_department_tree
        :param delete_missing: удалить из нашей БД отсутствующие более отделы
        """
        new_lookup = {}

        def collect(subtree):
            new_lookup[subtree['id']] = subtree
            for sub in subtree['children']:
                collect(sub)
        for root in tree:
            collect(root)

        new_ids = viewkeys(new_lookup)
        existing_departments = cls.objects.filter(portal_id=portal_id,
                                                  bitrix_id__in=new_ids)
        old_lookup = dict((dep.bitrix_id, dep) for dep in existing_departments)
        all_instances_lookup = old_lookup.copy()

        create_departments = []
        update_departments = []
        update_fields = 'name', 'sort', 'parent_id', 'head_id',
        mptt_fields = 'lft', 'rght', 'tree_id', 'level'

        for new_dep_info in itervalues(new_lookup):
            if new_dep_info['id'] not in old_lookup:
                department = cls(
                    bitrix_id=new_dep_info['id'],
                    portal_id=portal_id,
                )
                records = create_departments
            else:
                department = old_lookup[new_dep_info['id']]
                records = update_departments
            department.name = new_dep_info['name']
            department.head_id = new_dep_info['head_id']
            department.sort = new_dep_info['sort']

            def get_parent_delayed(parent_id):
                return lambda: parent_id and all_instances_lookup[parent_id]
            department._get_parent = \
                get_parent_delayed(new_dep_info['parent_id'])

            # fixme: непонятно, зачем обнуляем поля mptt
            for f in mptt_fields:
                setattr(department, f, 0)
            # fixme: вручную меняем значение tree_id. это ломает mptt
            department.tree_id = portal_id

            records.append(department)
            all_instances_lookup[department.bitrix_id] = department

        # mptt предположительно ломается, если слишком рано присвоить
        # инстансам родителей
        parents = dict(
            (dep.bitrix_id, dep._get_parent())
            for dep in create_departments + update_departments
        )

        for department in create_departments + update_departments:
            del department._get_parent

        def save(department):
            if getattr(department, '_saved', False):
                return
            parent = parents.get(department.bitrix_id)
            department.parent = parent
            if parent and not getattr(parent, '_saved', False):
                save(parent)
            # fix InvalidMove('Элемент не может быть потомком своего наследника.',)
            models.Model.save(department)
            department._saved = True

        for department in create_departments + update_departments:
            save(department)

        if delete_missing:
            cls.objects \
                .filter(portal_id=portal_id) \
                .exclude(bitrix_id__in=new_ids) \
                .delete()
        try:
            print('attempt to partially rebuild')
            cls.objects.partial_rebuild(tree_id=portal_id)
            print('partially rebuilt')
        except RuntimeError:
            # fixme: каждый раз попадаем сюда, потому что изменили tree_id
            print('partial rebuild failed')
            cls.objects.rebuild()

    @classmethod
    def _find_department_in_tree(cls, bitrix_id, tree):
        bitrix_id = int(bitrix_id)
        return first(cls._find_departments_in_tree(
            criteria_fn=lambda dep: dep['id'] == bitrix_id,
            tree=tree,
        ))

    @classmethod
    def _find_departments_in_tree(cls, criteria_fn, tree):
        for root in tree:
            if criteria_fn(root):
                yield root
            for subtree in root['children']:
                matches = cls._find_departments_in_tree(criteria_fn, [subtree])
                for department in matches:
                    yield department

    @classmethod
    def get_chatbot_departments(cls, token, bx_portal, **kwargs):
        """Возвращает подразделения чатботов на портале (если найдены)

        :type token: BitrixUserToken
        :type bx_portal: BitrixPortal
        :param kwargs: kwargs for BitrixPortal.get_department_tree

        :rtype: list[dict]
        :returns: подразделения, поля отделов аналогичны методу tree
        """
        # fixme: убираю вызов очень медленного get_department_tree
        #        побочный эффет в виде обновления подразделений портала перестанет работать
        # tree = bx_portal.get_department_tree(token, **kwargs)
        # return list(cls._find_departments_in_tree(
        #     lambda dep: dep['name'].lower().strip() in cls.CHATBOT_DEPARTMENTS,
        #     tree=tree,
        # ))

        bot_departments = token.call_list_method_v2('department.get', {'NAME': cls.CHATBOT_DEPARTMENTS})
        return [dict(
            id=int(dpt['ID']),
            name=dpt['NAME'],
            sort=dpt['SORT'],
            parent_id=int(dpt['PARENT']) if dpt.get('PARENT') else None,
        ) for dpt in bot_departments]
