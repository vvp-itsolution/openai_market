# -*- coding: UTF-8 -*-

import os

from django.conf.urls import url, include
# from django.conf import settings
# from django.conf.urls.static import static
from django.contrib import admin

from .views import (ArticleView, ArticleEdit, view_article_list,
                    view_change_article_dir, view_diffs, view_image_process,
                    view_article_search, view_main_article, view_logout_user,
                    view_get_article_render, view_auto_doc, article_tree, article_read)


admin.autodiscover()

PATH_TO_APP_STATIC = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'static')

urlpatterns = [
    url(r'^article_edit/(?P<pk>[0-9]+)/$', ArticleEdit.as_view(), name='article_edit'),
    url(r'^article_edit/$', ArticleEdit.as_view(), name='article_new'),
    url(r'^article/(?P<pk>[0-9]+)/$', ArticleView.as_view(), name='article'),
    url(r'^article/read/(?P<pk>[0-9]+)/$', article_read, name='article_read'),
    url(r'^diffs/(?P<pk>[0-9]+)/$', view_diffs, name='article_diffs'),
    url(r'^diffs/$', view_diffs, name='all_diffs'),
    url(r'^image_process/$', view_image_process, name='image_process'),
    url(r'^article_search/$', view_article_search, name='article_search'),
    url(r'^article_list/$', article_tree, name='article_list'),
    url(r'^get_article_render/$', view_get_article_render, name='get_article_render'),
    url(r'^fetch_docs/$', view_auto_doc, name='fetch_docs'),
    url(r'^article_tree/$', article_tree, name='article_tree'),
    url(r'^change_article_dir/$', view_change_article_dir, name='change_article_dir'),
    url(r'^logout/$', view_logout_user, name='logout'),
    # url(r'^static(?P<path>.*)$', 'django.views.static.serve', {
    #     'document_root': PATH_TO_APP_STATIC,
    # }),
    url(r'^api/v1/', include('its_utils.app_documentation.api.urls')),
    url(r'^$', view_main_article, name='main_article'),
]
