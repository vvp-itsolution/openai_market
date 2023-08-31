# coding: utf-8

from django.conf.urls import url

from its_utils.app_email.views import mark_tom

urlpatterns = [
    url('^marktom/(?P<tom_id>[0-9]+)_(?P<tom_hash>[a-z0-9]+)\.png$', mark_tom, name='mark_tom')
]
