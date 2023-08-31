# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import sys
try:
    from django.contrib.admin import ACTION_CHECKBOX_NAME
except ImportError:
    from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib import admin
from django.template.loader import get_template
from django.utils.safestring import mark_safe

import inspect

from requests import Request

PYTHON_VERSION = sys.version_info.major
STRING_TYPES = (str, unicode) if PYTHON_VERSION < 3 else (str,)

"""
В этом приложении мы будем хранить заготовки для удобной админки


Как настроить

1) наследуем модель админки от ActionAdmin

2) определяем переменную
actions = "action1", "action2"

3) одноименные методы должн быть описаны у модели

def action1(self):
    '''
        Так можно написать красивый текст который будет виден в админке
        :admin_action_description: Выполнить действие 1
    '''

    return "Ответ в виде текста"
"""


class ActionAdmin(admin.ModelAdmin):
    """
    Класс, который реализует "действия" на основе методов модели и класса модели в админке
    """

    def get_readonly_fields(self, request, obj=None):
        """
        Это мы перопределяем только чтобы добавить "поле" с кнопками внизу формы
        """

        fields = super(ActionAdmin, self).get_readonly_fields(request, obj)
        if obj:
            fields = list(fields) + ['entity_action']

        return fields

    def changelist_view(self, request, extra_context=None):
        """
        Костыль. Переопределяет changelist_view. Добавляет 0 в список отмеченных объектов, чтобы он стал непустым.
        """

        action = request.POST.get('action')
        if action:
            method = self.get_model_method(action)

            if method and self.is_class_or_static_method(action):
                if not request.POST.getlist(ACTION_CHECKBOX_NAME):
                    post = request.POST.copy()
                    post.update({ACTION_CHECKBOX_NAME: '0'})
                    request._set_post(post)

        return super(ActionAdmin, self).changelist_view(request, extra_context)

    def get_action(self, action):
        """
        Если action - имя метода модели, вернём model_action и описание функции
        """

        ex_action = super(ActionAdmin, self).get_action(action)
        if ex_action is None:
            method = self.get_model_method(action)

            if method:
                short_description = self.get_short_description_from_doc_string(method) or action
                ex_action = (ActionAdmin.model_action, action, short_description)

        return ex_action

    def get_model_method(self, name):
        return dict(inspect.getmembers(
            self.model, predicate=lambda m: (inspect.ismethod(m) or inspect.isfunction(m)) and m.__name__ == name
        )).get(name)

    @staticmethod
    def get_short_description_from_doc_string(func):
        """
        Получить короткое описание из документации функции
        """

        doc = func.__doc__
        name = func.__name__

        if doc:
            for doc_str in doc.split('\n'):
                doc_str = doc_str.strip()
                if doc_str.startswith(':admin_action_description'):
                    return doc_str[26:].strip()

        return name.replace('_', ' ').capitalize()

    def is_class_or_static_method(self, name):
        """
        Проверить, является ли метод classmethod'ом или static-методом
        """
        for cls in self.model.__mro__:
            if isinstance(cls.__dict__.get(name, 'string type'), (classmethod, staticmethod)):
                return True
        return False


    def model_action(self, request, queryset):
        """
        Выполнение метода класса
        """

        # 1) определить что за акшион
        action = request.POST.get('action')

        # 2) найти функцию
        method = self.get_model_method(action)

        if self.is_class_or_static_method(action):
            result = method()
            if isinstance(result, (list, tuple)):
                result = "<br>".join(result)

            if isinstance(result, STRING_TYPES):
                res = u'<strong>Результат действия:</strong><br> %s' % result.replace('\n', '<br>')
                self.message_user(request, mark_safe(res))

            else:
                return result

        else:
            res = []
            for obj in queryset:
                if hasattr(obj, '__unicode__'):
                    obj_repr = obj.__unicode__()

                elif hasattr(obj, '__str__'):
                    obj_repr = obj.__str__()

                else:
                    obj_repr = u'id{}'.format(obj.id)

                res.append(u'{}: {}'.format(obj_repr, method(obj)))

            self.message_user(request, mark_safe(u'<br><br>'.join(res)))

    def entity_action(self, obj):
        """
        Поле с к нопками
        """

        entity_name = obj._meta.model_name

        # Чтобы получить действия, нужно передать любой Request c полями GET и META
        request = Request('get', 'http://it-solution/admin/')
        request.GET = {}
        request.META = {}

        from django.contrib.auth.models import AnonymousUser
        request.user = AnonymousUser()

        actions = filter(lambda a: a[0] != 'delete_selected', self.get_action_choices(request))

        return get_template('app_admin/entity_action.html').render({
            'entity_name': entity_name,
            'entity_id': obj.pk,
            'actions': actions
        })

    entity_action.short_description = mark_safe(u'<strong>Действие</strong>')

    def response_action(self, request, queryset):
        """
        Если действие выполнялось из формы изменения, перенаправлять не на список, а на ту же форму
        """

        if request._post.get('_infoblock_entity_action'):
            request.path += '%s/' % request._post.get('_selected_action')

        return super(ActionAdmin, self).response_action(request, queryset)
