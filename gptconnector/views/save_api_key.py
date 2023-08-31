from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from bitrix_utils.bitrix_auth.market_auth.auth_on_user_token_sig import auth_on_user_token_sig
from gptconnector.models import PortalSettingsGptConnector
from integration_utils.its_utils.app_get_params import get_params_from_sources


@csrf_exempt
@get_params_from_sources
def save_api_key(request):

    x = request.GET['api_key']
    rd = auth_on_user_token_sig(request)
    print(x)
    print(rd)

    #if rd.bitrix_user.is_admin:
    #     ps = PortalSettingsGptConnector.by_portal(rd.bitrix_portal)
    #     ps.gpt_api_key = request.its_params.get('api_key')
    #     ps.save()

    return HttpResponse("ok")
