#coding: utf-8
from django.http import HttpResponse
from its_utils.app_logging.cron_functions import handle_redis_logs


def view_test_redis_logging(request):
    import logging
    logging.getLogger('its.redis').debug('test debug')
    logging.getLogger('its.redis').info('test info')
    logging.getLogger('its.redis').warning('test warning')
    logging.getLogger('its.redis').error('test error')
    logging.getLogger('its.redis').critical('test critical')

    handle_redis_logs()

    return HttpResponse("ok")