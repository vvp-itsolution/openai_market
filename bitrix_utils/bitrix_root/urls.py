from django.urls import path

from bitrix_utils.bitrix_root.views.set_payment import set_payment

urlpatterns = [
    path('set_payment/', set_payment),
]
