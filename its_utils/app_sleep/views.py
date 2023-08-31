#coding=utf-8
import time
from django.http import HttpResponse


def view_sleep(request):

    seconds = int(request.GET.get('seconds', 1))
    time.sleep(seconds)

    return HttpResponse('response after %s sec' % seconds)