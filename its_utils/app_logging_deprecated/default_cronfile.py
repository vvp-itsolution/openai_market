#!/usr/bin/env python
# coding=utf-8
"""Пример того как должен выглядеть кронфайл"""
import sys
import os
import django

FILE_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(FILE_PATH, '../../'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

# django.setup() требуется только для версий django >=1.7
try:
    django.setup()
except AttributeError:
    pass

from its_utils.app_logging.cron_functions import handle_redis_logs
from its_utils.functions import get_lock
from django.conf import settings

if __name__ == '__main__':
    if hasattr(settings, 'PROJECT_NAME'):
        project_name = settings.PROJECT_NAME
    else:
        project_name = "no_project_name"

    get_lock('%s_itsutils_app_logging_lock' % project_name)
    handle_redis_logs()