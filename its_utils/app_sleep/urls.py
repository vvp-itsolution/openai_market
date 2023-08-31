#coding: utf-8

from django.conf.urls import url
from its_utils.app_sleep.views import view_sleep

urlpatterns = [
    url('^sleep/$', view_sleep, name='sleep')
]