#coding: utf-8

from django.conf.urls import url
from its_utils.app_logging.view_test_redis_logging import view_test_redis_logging
from its_utils.app_logging.views.view_test_redis_logging import showlog

urlpatterns = [
    url('^test_redis_logging/$', view_test_redis_logging, name='test_redis_logging'),
    url('^showlog/$', showlog)
]