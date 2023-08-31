#coding=utf-8
import json
from django.conf import settings
from django.http import HttpResponse

from its_utils.app_get_params import get_params_from_sources
from its_utils.functions import sys_call

@get_params_from_sources
def view_syscall(request):
    if not request.user.is_superuser:
        #TODO переделать
        return 3
    #if request.META.method == 'POST':
    call = request.its_params.get('call')
    password = request.its_params.get('password', None)
    if not password or password != settings.SYS_CALL_PASSWORD:
        return HttpResponse('{"response":"error wrong password"}')
    res, output = sys_call(call)
    text = "%s \n\r\n\r %s" % (res, output)
    return HttpResponse(text)

    #if request.META.method == 'GET':
