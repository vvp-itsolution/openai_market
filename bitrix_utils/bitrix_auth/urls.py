# -*- coding: UTF-8 -*-

from django.conf.urls import url
from bitrix_utils.bitrix_auth.views import test_page
from bitrix_utils.bitrix_auth.api import *


urlpatterns = [
    url(r'^test_bitrix_auth/?$', test_page, name='test_page'),


    url(r'^access_object_set\.save/?$', access_object_set_save, name='access_object_set_save'),
    url(r'^access_object_set\.get/?$', access_object_set_get, name='access_object_set_save'),
    url(r'^access_object_set\.get_list/?$', access_object_set_get_list, name='access_object_set_get_list'),
]
