import pickle

from django.conf import settings
from django_redis import get_redis_connection

redis = get_redis_connection('redis')

def call_task(task):
    func, args, kwargs = pickle.loads(task)
    func(*args, **kwargs)
    return str(func)


def call_next():
    dumped_task = redis.rpop('{}.tasks'.format(settings.ITS_LOG_PREFIX))
    if dumped_task:
        return call_task(dumped_task)
    else:
        return False


def call_all(max_count=20):
    count = 0
    results = []
    while True:
        result = call_next()
        if not result:
            break
        results.append(result)
        count += 1
        if count >= max_count:
            break

    return results