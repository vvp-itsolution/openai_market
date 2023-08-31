from django.urls import path

from base_market_application.views.index import index

urlpatterns = [
    path('', index),
]
