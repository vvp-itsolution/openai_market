# -*- coding: UTF-8 -*-

from django.db import models
from django.db.models import Case, When, CharField, Value as V
from django.db.models.functions import Concat, Cast


class BitrixAccessObjectSet(models.Model):

    """
    Представляет собой конкретное правило для одного объекта.
    Объекты должны ссылатся на эту модель, чтобы получить функцию управления доступом.
    """
    INVALID_RULE = '[INVALID/UNKNOWN]'

    class Meta:
        app_label = 'bitrix_auth'

    def __unicode__(self):
        return u'AccessSet %s' % self.id

    def as_access_array(self, as_queryset=False, errors='strip'):
        from . import BitrixAccessObject

        assert errors in ('strip', 'include')
        rules = self.bitrixaccessobject_set.annotate(rule=Case(
            When(type=BitrixAccessObject.SYSTEM_GROUP,
                 type_id=BitrixAccessObject.ALL_USERS,
                 then=V('UA')),
            When(type=BitrixAccessObject.USER,
                 then=Concat(V('U'), Cast('type_id', CharField()))),
            When(type=BitrixAccessObject.GROUP,
                 then=Concat(V('SG'), Cast('type_id', CharField()))),
            When(type=BitrixAccessObject.DEPARTMENT,
                 then=Concat(V('DR'), Cast('type_id', CharField()))),
            default=V(self.INVALID_RULE),
            output_field=CharField(),
        )).values('rule')
        if errors == 'strip':
            rules = rules.exclude(rule=self.INVALID_RULE)
        if as_queryset:
            return rules
        return list(rules.values_list('rule', flat=True))
