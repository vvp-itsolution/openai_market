#coding: utf-8
from django.conf import settings
from django.http import HttpResponse
from django_redis import get_redis_connection

from its_utils.app_logging.cron_functions import handle_redis_logs

from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_superuser)
def showlog(request):

    q_name = "{}.its_logging.log".format(getattr(settings, 'ITS_LOG_PREFIX', ''))

    redis = get_redis_connection("redis")
    logs = redis.lrange(q_name, 0, 1000)


    return HttpResponse(logs)