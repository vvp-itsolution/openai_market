# Файл такой же как local_settings, но эта часть хранит не локальные настройки, а разные пароли
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'market_framework',
        'USER': 'market_framework',
        'PASSWORD': '1111111111111111111111111111111111111111',
        'HOST': '188.124.41.43',
    },
}


SECRET_KEY = 'changeme'
SALT = 'changeme'


EMAIL_HOST = 'localhost'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
SERVER_EMAIL = 'ma@ma.it-solution.ru'