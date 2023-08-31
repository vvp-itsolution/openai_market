# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

from collections import Counter

from django.contrib import admin
from django.utils.safestring import mark_safe


class BackRelAdmin(admin.ModelAdmin):
    """
    Класс добавляет ссылки на все модели, которые ссылаются на модель админки
    """

    def get_readonly_fields(self, request, obj=None):
        fields = list(super(BackRelAdmin, self).get_readonly_fields(request, obj))
        fields.append('back_rel_fields')

        return fields

    def back_rel_fields(self, obj):
        relations = self.model._meta.related_objects
        counter = Counter([r.related_model for r in relations])
        links = []

        for rel in relations:
            links.append(
                '<a style="border-radius: 4px; padding: 2px 5px; margin-left: 2px; background-color: '
                '#eef3f4" target="_blank" href="/admin/{app}/{model}/?{field}__id__exact={obj_id}">'
                '{model_title}{field_name}</a>'.format(
                    app=rel.related_model._meta.app_config.name,
                    model=rel.related_model._meta.model_name,
                    field=rel.field.name,
                    obj_id=obj.id,
                    model_title=rel.related_model._meta.verbose_name_plural.title(),
                    field_name=' (%s)' % rel.field.verbose_name if counter[rel.related_model] > 1 else ''
                )
            )

        return mark_safe(''.join(links))

    back_rel_fields.short_description = 'Связанные модели'
