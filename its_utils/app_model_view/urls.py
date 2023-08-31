# -*- coding: UTF-8 -*-

from django.conf.urls import url, include

from its_utils.app_model_view import views

urlpatterns = [
    url(r'^api/', include('its_utils.app_model_view.api.urls')),
    url(r'^(?P<app>.*?)/(?P<model_name>.*?)/?$', views.model_detail, name='model_detail'),
    url(r'^/?$', views.model_list, name='model_page'),
]
