# -*- coding: UTF-8 -*-

from django.conf.urls import url


from its_utils.app_model_view.api import *


urlpatterns = [
    url(r'^get_model_fields/?$', get_model_fields, name='get_model_fields'),
    url(r'^get_model_fields_for_foreign/?$', get_model_fields_for_foreign, name='get_model_fields_for_foreign'),
    url(r'^get_model_data/?$', get_model_data, name='get_model_data'),
    url(r'^get_app_models/?$', get_app_models, name='get_app_models'),
    url(r'^get_project_apps/?$', get_project_apps, name='get_project_apps'),
    url(r'^get_apps_and_models/?$', get_apps_and_models, name='get_apps_and_models'),
    url(r'^export/?$', export, name='export'),
]
