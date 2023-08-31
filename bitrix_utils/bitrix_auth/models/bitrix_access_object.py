# -*- coding: UTF-8 -*-

from django.db import models


class BitrixAccessObject(models.Model):

    """
    Конкретное правило. Может быть использовано для пользователя, отдела и группы - параметр type.
    type_id показывает какой именно объект входит в этом правило.
    Т.е. BitrixAccessObject(type=USER, type_id=1, set_id=3)
    означает что пользователь с bitrix_id 1 будет иметь доступ к объекту, который ссылается на правило под id 3

    Особый тип - SYSTEM_GROUP. Это системные группы, которые не подходят ни под один тип. Например, "Все пользователи".
    """

    USER = 0
    GROUP = 1
    DEPARTMENT = 2
    SYSTEM_GROUP = 3

    TYPES = (
        (USER, 'user',),
        (GROUP, 'group'),
        (DEPARTMENT, 'department'),
        (SYSTEM_GROUP, 'system_group'),
    )

    ALL_USERS = 0

    set = models.ForeignKey('bitrix_auth.BitrixAccessObjectSet', on_delete=models.CASCADE)
    type = models.PositiveSmallIntegerField(choices=TYPES)
    type_id = models.IntegerField()

    class Meta:
        app_label = 'bitrix_auth'

    def __unicode__(self):
        return u'%s (%s %s)' % (self.set, self.TYPES[self.type][1], self.type_id)
