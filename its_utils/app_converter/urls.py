# -*- coding: UTF-8 -*-

from django.conf.urls import url

from .views import csv_to_xls


urlpatterns = [
    url(r'csv_to_xls/?$', csv_to_xls, name='csv_to_xls'),
]
