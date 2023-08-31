from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin


def base_urls(urls):
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('its/', include('its_utils.app_error.urls')),
        path('its/', include('integration_utils.its_utils.app_gitpull.urls')),
        path('its/', include('its_utils.app_cron.urls')),
    ]

    urls['urlpatterns'] += urlpatterns

    urls['handler500'] = 'its_utils.app_error.views.error_500_info.error_500_info'

    urls['urlpatterns'] += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urls['urlpatterns'] += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)