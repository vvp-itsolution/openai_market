# -*- coding: UTF-8 -*-

import django

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.apps import apps


def get_models_django_19(name):
    if name == 'contrib':
        raise StopIteration
    module = apps.get_app_config(name).models_module
    for d in dir(module):
        model = getattr(module, d)
        if issubclass(type(model), models.base.ModelBase):
            yield model


def get_models_django_18(name):
    try:
        app = models.get_app(name)
    except ImproperlyConfigured:
        return []

    return models.get_models(app)

def get_model_fields(model):
    version = django.get_version().split('.')
    if int(version[0]) > 0:
        v = int(version[1])
        if v in (7,):
            return model._meta.get_all_field_names()
        return model._meta.get_fields()

version = django.get_version().split('.')

if int(version[0]) > 0:
    v0, v1 = int(version[0]), int(version[1])
    if v0 > 1 or v1 >= 9:
        get_models = get_models_django_19

    if v1 in (7, 8) :
        get_models = get_models_django_18
