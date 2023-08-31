import threading
import time

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse

from django.views.decorators.csrf import csrf_exempt
from requests import Timeout

from bitrix_utils.bitrix_auth.models import BitrixPortal
from gptconnector.models.ai_tasks import AiTask
from integration_utils.its_utils.app_get_params import get_params_from_sources


def prepair_response(callback_url, prompt):
    time.sleep(3)
    qq = requests.post(callback_url, json={"result": ['Привет1111))))']})

def delayed_processing():
    # задача этй функции в дергнуть вебхук и забыть про него, эмулятор конвейера
    time.sleep(0.1)
    try:
        requests.post(f"https://{settings.DOMAIN}/gptconnector/process_tasks/", timeout=0.1)
    except Timeout:
        pass



@csrf_exempt
@get_params_from_sources
def handle_request(request):

    callback_url = request.its_params.get('callbackUrl')
    if not callback_url:
        # битрикс стучит для проверки хендлера
        return HttpResponse("")
    prompt = request.its_params.get('prompt')

    from urllib.parse import urlparse
    parsed_url = urlparse(callback_url)
    domain = parsed_url.netloc

    ai_task = AiTask.objects.create(prompt=prompt, callback_url=callback_url, portal=BitrixPortal.objects.get(domain=domain))

    #threading.Thread(target=prepair_response, args=[callback_url, prompt]).start()

    # По условиям API мы должны быстро вернуть ответ об успешной постановке задаче в очередь, а обработку сделать через очередь
    # В очередь мы положили задание, но его вызов будем делать не на кроне, а на http запросе, альтернатива крону
    #threading.Thread(target=delayed_processing).start()

    threading.Thread(target=ai_task.process).start()


    return JsonResponse({'result':'OK'}, status=202)

