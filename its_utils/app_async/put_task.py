import pickle

from django.conf import settings
from django_redis import get_redis_connection


def put_task(func, *args, **kwargs):
    redis = get_redis_connection('redis')
    redis.rpush('{}.tasks'.format(settings.ITS_LOG_PREFIX), pickle.dumps((func, args, kwargs)))


