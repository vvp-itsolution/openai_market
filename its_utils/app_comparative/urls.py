# -*- coding: UTF-8 -*-

from django.conf.urls import url


from views.compare_view import compare
from views.split_html import split

urlpatterns = [
    url(r'compare/(\d+)/?$', compare),
    url(r'^split_html/', split),

]
