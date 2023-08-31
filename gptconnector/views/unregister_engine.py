from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from bitrix_utils.bitrix_auth.market_auth.auth_on_user_token_sig import auth_on_user_token_sig



@csrf_exempt
def unregister_engine(request):
    rd = auth_on_user_token_sig(request)
    if rd.bitrix_user.is_admin:
        but = rd.bitrix_user_token
        but.call_api_method('ai.engine.unregister', {
            'code': 'gptconnector',
        })

    return JsonResponse({"result": "ok"})
