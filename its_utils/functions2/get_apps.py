# -*- coding: UTF-8 -*-

from django.apps import apps


def get_apps():

    return [x for x in apps.app_configs.keys()]