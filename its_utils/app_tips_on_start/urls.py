# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import api


urlpatterns = [
    url(r'^$', api.tip_list, name='tips'),
    url(r'^(?P<tip_id>\d+)/$', api.tip_get, name='tip'),
    url(r'^category/(?P<category_id>\d+)/$', api.tip_list, name='tips_by_category'),
]
