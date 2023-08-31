from django.conf import settings as django_settings

ITS_ASSETS_UPLOAD_TO = getattr(django_settings, 'ITS_ASSETS_UPLOAD_TO', 'assets')