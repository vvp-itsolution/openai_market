from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from bitrix_utils.bitrix_auth.market_auth.auth_on_user_token_sig import auth_on_user_token_sig
from gptconnector.models import AiTask


@csrf_exempt
def process_tasks(request):
    # Вью для отложенного запуска обработки заданий
    AiTask.process_all()
    return JsonResponse({"result": "ok"})
