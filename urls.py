from django.urls import path, include

urlpatterns = [
    path('base_market_application/', include('base_market_application.urls')),
    path('gptconnector/', include('gptconnector.urls')),
]

from its_utils.base_urls import base_urls
base_urls(locals())



