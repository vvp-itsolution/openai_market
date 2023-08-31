# -*- coding: UTF-8 -*-

import django

def get_model(app, model):
    pass

def get_model_django_19(app, model):
    from django.apps import apps

    try:
        return apps.get_model(app, model)
    except LookupError:
        return


def get_model_django_18(app, model):
    from django.db.models.loading import get_model
    try:
        return get_model(app, model)
    except LookupError:
        return


version = django.get_version().split('.')

if 2 > int(version[0]) > 0:
    v = int(version[1])
    if v >= 9:
        get_model = get_model_django_19

    if v == 8:
        get_model = get_model_django_18
elif int(version[0]) == 2:
    v = int(version[1])
    if v >= 0:
        get_model = get_model_django_19
