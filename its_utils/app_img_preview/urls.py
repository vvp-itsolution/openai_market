#coding: utf-8
from django.urls import path

from its_utils.app_img_preview.views import view_img_preview

urlpatterns = [
    path('img_preview/', view_img_preview, name='img_preview')
]