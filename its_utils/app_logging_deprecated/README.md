#TODO для
from django.utils.log import DEFAULT_LOGGING
LOGGING = DEFAULT_LOGGING

###Добавление логгера its.redis к существующим настройкам

1) установить редис, если нету

2) pip install django_redis, если нету

3) внутри **settings.py**

3.1) добавить в импорты
from its_utils.app_logging.default_logging_settings import attach_logger

3.2) Добавить в **INSTALLED_APPS**  'its_utils.app_logging'

3.3) после конфигурации **LOGGING**=... добавить
ITS_LOG_LEVEL = 'DEBUG' # желаемый уровень логирования
attach_logger(LOGGING, 'its.redis', ITS_LOG_LEVEL)

4) внутри **local_settings.py**

4.1) удостовериться, что редис прописан в **CACHES** по адресу
'redis': {...его настройки...},

```
CACHES = {
    'redis': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': '192.168.0.151:6379:5',
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'PASSWORD': 'апукауцауцуа',
            },
    }
}
```

5) выполнить **manage.py migrate** (syncdb на старой джанге)

#TODO использовать с cron логгинг
6) скопировать(или просто прописать путь к этому файлу) /папка-проекта/its_utils/app_logging/default_cronfile.py
например как /папка-проекта/cron_redis_logs.py

6.1) прописать его в **crontab** на каждую минуту


###Как протестировать в браузере

1) в **urls.py** добавить, например
url(r'^its-test/', include('its_utils.app_logging.urls')),

2) зайти на /its-test/test_redis_logging/
должны создаться тестовые записи в логе и на почте
/admin/app_logging/logfromredis/

###Как использовать в проектах
1) import logging
2) logging.getLogger('its.redis').debug('test debug')


###Как протестировать в консоли

1) import logging
2) logging.getLogger('its.redis').debug('test debug')


###Использование в скриптах (например cron)
* * * * * sudo -u www-data python /home/chess_django/cron_for_gs_endgame_processing.py --log-level=WARNING
--log-level=WARNING - переназначает уровень логгинга несмотря на файл settings.py