from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from bitrix_utils.bitrix_auth.market_auth.auth_on_iframe_start import auth_on_iframe_start

@csrf_exempt
def index(request):
    #return HttpResponse("f")
    rd = auth_on_iframe_start(request)

    return render(request, 'index.html', locals())
