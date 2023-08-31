# -*- coding: UTF-8 -*-

from django.conf.urls import url

from . import article_get_list, article_get_raw, article_save


urlpatterns = [
    url('article.get_list/$', article_get_list, name='article_get_list'),
    url('article.get_raw/$', article_get_raw, name='article_get_raw'),
    url('article.save/$', article_save, name='article_save'),
]
