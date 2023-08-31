
import os
from django.conf.urls import patterns, url

PATH_TO_APP_STATIC = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'static')

urlpatterns = patterns('its_utils.app_linuxshell.views',
    url(r'^execute/$', 'view_execute_script', name='execute-script'),
) + patterns('',
    url(r'^static(?P<path>.*)$', 'django.views.static.serve', {
        'document_root': PATH_TO_APP_STATIC,
    }))