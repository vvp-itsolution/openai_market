###Как использовать
1) В settings.py в CACHES добавить 'redis', если его там нет. Это может выглядеть так:

    CACHES = {
        'redis': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': '192.168.1.1',
            'OPTIONS': {
                'PASSWORD': 'PASS',
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
        },
    }

2) В settings.py в LOGGING['filters'] добавить фильтр

        'mail_filter_limit_to_send': {
            '()': 'its_utils.app_mail_filter.filter.MailFilterLimitToSend'
        }

3) Найти или добавить в LOGGING['handlers'] django logging handler где в 'class' прописан 'django.utils.log.AdminEmailHandler', для примера
это может выглядеть так:


    'handlers': {
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler'
            }
        }
        
И добавить 'mail_filter_limit_to_send' в ему в filters, например так

    'handlers': {
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false', 'mail_filter_limit_to_send'],
                'class': 'django.utils.log.AdminEmailHandler'
            }
        }