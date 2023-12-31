from django.apps import apps
from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered

from its_utils.app_admin.functions import override_json_form_field
from settings import ilogger

"""
Если у модели есть подкласс Admin
то этот скрипт автоматически подкючает в админку все такие модели из приложения app_name
возьмите файл _admin.py и перенесите в папку с приложением с именем admin.py
"""


def auto_register(app_name):
    for model in apps.get_app_config(app_name).get_models():
        # if RuntimeError: OrderedDict mutated during iteration check ./models/__init__.py
        try:
            admin_cls = getattr(model, 'Admin', None)
            if not admin_cls:
                continue

            # добавить виджет prettyjson
            override_json_form_field(admin_cls)

            if hasattr(admin_cls, 'before_register'):
                admin_cls.before_register()

            admin.site.register(model, admin_cls)

        except AlreadyRegistered as exc:
            ilogger.warning('model_admin_already_registered', 'model_admin_already_registered')
