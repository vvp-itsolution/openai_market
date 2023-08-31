# -*- coding: utf-8 -*-
from django.urls import path

from its_utils.app_cron.views import *


urlpatterns = [
    path('run_cron/<int:pk>/', run_cron, name='run_cron'),
    path('cron/<int:pk>/', cron_view, name='cron_view'),
]
