from django.urls import path
from . import views

app_name = 'bitrix_telegram_log'

urlpatterns = [
    path('btl/start_binding/', views.start_binding, name='start_binding'),
    path('btl/ping/', views.ping, name='ping'),
]
