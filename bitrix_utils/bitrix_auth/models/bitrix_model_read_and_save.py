# -*- coding: UTF-8 -*-

from django.db import models

from bitrix_utils.bitrix_auth.models import BitrixAccessObject
from bitrix_utils.bitrix_auth.models import BitrixAccessObjectSet


class BitrixModelReadAndSave(models.Model):

    DEFAULT_READ_ACCESS_OBJECT_TYPE = BitrixAccessObject.SYSTEM_GROUP
    DEFAULT_READ_ACCESS_OBJECT_TYPE_ID = BitrixAccessObject.ALL_USERS

    read_access = models.ForeignKey('bitrix_auth.BitrixAccessObjectSet', related_name='article_read',
                                    on_delete=models.PROTECT)
    save_access = models.ForeignKey('bitrix_auth.BitrixAccessObjectSet', related_name='article_save',
                                    on_delete=models.PROTECT)

    class Meta:
        app_label = 'bitrix_auth'
        abstract = True

    def save(self, editor=None, *args, **kwargs):
        if not self.pk and not self.save_access_id:
            self.read_access_id = BitrixAccessObjectSet.objects.create().id
            BitrixAccessObject.objects.create(
                set_id=self.read_access_id,
                type=self.DEFAULT_READ_ACCESS_OBJECT_TYPE,
                type_id=self.DEFAULT_READ_ACCESS_OBJECT_TYPE_ID
            )

            self.save_access_id = BitrixAccessObjectSet.objects.create().id
            BitrixAccessObject.objects.create(
                set_id=self.save_access_id,
                type=BitrixAccessObject.USER,
                type_id=self.user.bitrix_id
            )
        if editor is not None:
            BitrixAccessObject.objects.get_or_create(
                set_id=self.save_access_id,
                type=BitrixAccessObject.USER,
                type_id=editor.bitrix_id
            )

        super(BitrixModelReadAndSave, self).save(*args, **kwargs)

    @classmethod
    def with_access(cls, access_type, bx_user, qs=None, app_name=None):
        """queryset с фильтром по правам доступа,
        учитывает группы и подразделения пользователя
        :param access_type 'read' или 'save'
        :param bx_user BitrixUser instance фильтруем по правам для этого пользователя
        :param qs queryset для фильтрации или None для cls.objects.all()
        :param app_name опционально имя приложения или список имен приложений
        :return queryset
        """
        if access_type == 'read':
            access_object_set_field = 'read_access'
        elif access_type == 'save':
            access_object_set_field = 'save_access'
        else:
            raise ValueError(u"access_type может быть только 'save' и 'read', "
                             u"передано {!r}".format(access_type))

        if qs is None:
            qs = cls.objects.all()

        groups, departments = \
            bx_user.get_groups_and_departments(app_name=app_name)

        access_objects = BitrixAccessObject.objects.filter(
            # Объекты доступа для пользователя
            models.Q(type=BitrixAccessObject.USER, type_id=bx_user.bitrix_id) |
            # + Объекты доступа для любой группы пользователя
            models.Q(type=BitrixAccessObject.GROUP, type_id__in=groups) |
            # + Объекты доступа для любого департамента пользователя
            models.Q(type=BitrixAccessObject.DEPARTMENT,
                     type_id__in=departments) |
            # + Объект доступа "Для всех"
            models.Q(type=BitrixAccessObject.SYSTEM_GROUP,
                     type_id=BitrixAccessObject.ALL_USERS)
        ).filter(
            # Только со связанными BitrixAccessObjectSet
            set=models.OuterRef(access_object_set_field),
        )
        return qs \
            .annotate(has_access=models.Exists(access_objects.only('id'))) \
            .filter(has_access=True)

    @classmethod
    def with_read_access(cls, bx_user, qs=None, app_name=None):
        """Объекты с правами доступа на чтение для переданного пользователя
        :param bx_user BitrixUser instance фильтруем по правам для этого пользователя
        :param qs queryset для фильтрации или None для cls.objects.all()
        :param app_name опционально имя приложения или список имен приложений
        :return: queryset
        """
        return cls.with_access('read', bx_user, qs, app_name)

    @classmethod
    def with_save_access(cls, bx_user, qs=None, app_name=None):
        """Объекты с правами доступа на сохранение/редактирование для переданного пользователя
        :param bx_user BitrixUser instance фильтруем по правам для этого пользователя
        :param qs queryset для фильтрации или None для cls.objects.all()
        :param app_name опционально имя приложения или список имен приложений
        :return: queryset
        """
        return cls.with_access('save', bx_user, qs, app_name)
