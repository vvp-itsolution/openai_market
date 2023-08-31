from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils import timezone

from bitrix_utils.bitrix_auth.market_auth.request_data import RequestData
from bitrix_utils.bitrix_auth.models import BitrixUserToken, BitrixUser


def auth_on_iframe_start(request):
    # Возвращает RequestData или false
    # true - если вход через iframe запуска приложения (во стройках тоже работает)
    # на базе разнообразных параметров в iframe определяет пользователя и сохраняет в request
    #
    #request.bitrix_user
    #request.bitrix_user_is_new
    #request.bitrix_user_token

    rd = RequestData()
    rd.from_iframe_data(request)
    rd.fill_portal_data()
    rd.fill_from_batch()
    rd.check_app_data()
    rd.fill_portal()
    rd.fill_user()
    rd.fill_token()

    request.request_data = rd

    return rd
