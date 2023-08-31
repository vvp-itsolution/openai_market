#coding: utf-8

from django.conf.urls import url
from its_utils.app_tests.views import *

urlpatterns = [
    url('^500/$', view_error_500, name='error500'),
    url('^get_locales/$', view_get_locales, name='get_locales'),
    url('^syscall/$', view_syscall, name='syscall'),
]