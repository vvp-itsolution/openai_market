# coding=utf-8
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
from django_redis import get_redis_connection
import time

"""
ExpirationList оснванный на http://redis.io/commands#sorted_set

1) этот лист expirится вручную!!!
2) Можно пользоватся как обычными ключами???
ex_list = ExpirationList('redis', 'ГруппаКлючей')

"""

class ExpirationList(object):
    def __init__(self, alias='default', object_name='expiration_list', tte=60000):
        self.redis = get_redis_connection(alias)
        self.object_name = object_name
        #time to expire
        self.tte = tte # в миллисекундах
        #Время на которое дольше храним экземпляр даннах
        self.additional_time = 60 #в секундах

    def add(self, item, value=None, expire=None):
        if not expire:
            expire = self.tte
        if value:
            self.redis.set("%s:%s" % (self.object_name, item), value)
            self.redis.expire("%s:%s" % (self.object_name, item), expire/1000+60)
        return self.redis.zadd(self.object_name, {item:int(time.time()*1000) + expire})

    def get(self, item, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time()*1000)
        #1) взять по ключу
        value = self.redis.get("%s:%s" % (self.object_name, item))
        #2) найти в сортед сете
        ttl = max(-1, timestamp - self.redis.zscore(self.object_name, item))

        return value, ttl

    def postpone(self, item, expire=None):
        if not expire:
            expire = self.tte
        #Окладываем исчезновение экземпляра данных
        if self.redis.exists("%s:%s".format(self.object_name, item)):
            self.redis.expire("%s:%s".format(self.object_name, item), expire/1000+60)
        return self.add(item, None, expire=expire)

    def get_expired(self, limit=None, remove=False, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time()*1000)
        items = self.redis.zrangebyscore(self.object_name, 0, timestamp)

        if limit:
            items = items[:limit]

        if remove and not limit:
            self.delete_expired(timestamp)
        elif remove and limit:
            for item in items:
                self.delete(item)
        else:
            pass
        return items

    def delete_expired(self, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time()*1000)
        return self.redis.zremrangebyscore(self.object_name, 0, timestamp)

    def delete(self, item):
        return self.redis.zrem(self.object_name, item)

    def get_all(self):
        return self.redis.zrange(self.object_name, 0, -1)

    def count(self):
        return self.redis.zcard(self.object_name)


if __name__ == '__main__':
    ex_list = ExpirationList('local_gs')
    print('-------------------------------')
    print('add new item with expire=2 sec')
    ex_list.add('item', None, 2000)
    print('expired items')
    ex = ex_list.get_expired()
    print(ex)
    print('sleep 2 sec')
    time.sleep(2)
    print('expired items')
    ex = ex_list.get_expired()
    print(ex)
    print('-------------------------------')
    print('*******************************')
    print('-------------------------------')
    print('set expire=2 for item')
    ex_list.postpone('item', 2000)
    print('expired items')
    ex = ex_list.get_expired()
    print(ex)
    print('sleep 2 sec')
    time.sleep(2)
    print('-------------------------------')
    print('*******************************')
    print('-------------------------------')
    tt = int(time.time()*1000)
    print('expired items by timestamp %s' % tt)
    ex = ex_list.get_expired(None, None, tt)
    print(ex)
    print('remove expired items by timestamp %s' % tt)
    ex_list.delete_expired(tt)
    print('expired items by timestamp %s' % tt)
    ex = ex_list.get_expired(None, None, tt)
    print(ex)
    print('-------------------------------')
    print('*******************************')
    print('-------------------------------')
    print('add 4 items')
    for i in range(1, 5):
        ex_list.add('item%s' % i, None, 2000)
    print('get count of elements')
    ex = ex_list.count()
    print('count of elements in set')
    print(ex)
    print('-------------------------------')
    print('*******************************')
    print('-------------------------------')
    print('get all')
    ex = ex_list.get_all()
    print(ex)
    print('-------------------------------')
    print('*******************************')
    print('-------------------------------')
    print('remove all')
    for item in ex:
        ex_list.delete(item)
    print('get all')
    ex = ex_list.get_all()
    print(ex)
    print('-------------------------------')