# -*- coding: UTF-8 -*-

import traceback
import json
import importlib

from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import render

from its_utils.app_cron.models import Cron, CronResult


def run_cron(request, pk):

    if getattr(settings, 'ITS_START_CRON_SECRET', None) and request.GET.get('secret','') == settings.ITS_START_CRON_SECRET:
        #Если подписали секретом, то и пусть
        #Это может понадобиться для newrelic кронов
        pass
    else:
        if not request.user.is_superuser:
            return HttpResponse('Only superuser allowed', status=400)

        if request.method != 'POST':
            return HttpResponse('Only POST allowed', status=400)

    start = timezone.now()
    try:
        cron = Cron.objects.get(id=pk)
    except Cron.DoesNotExist:
        return HttpResponse('Cron with id %s was not found' % pk)

    messages = []
    last_dot_index = cron.path.rfind('.')
    module, function = cron.path[:last_dot_index], cron.path[last_dot_index + 1:]
    messages.append(u'Trying to run %s: %s' % (cron, cron.path))
    result = None

    try:
        module = importlib.import_module(module)
    except ImportError:
        messages.append(traceback.format_exc())
    else:
        function = getattr(module, function)
        if not (function and callable(function)):
            messages.append(u'Bad function')
        else:
            try:
                if cron.parameters:
                    parameters = json.loads(cron.parameters)
                else:
                    parameters = {}
                result = function(**parameters)
            except Exception:
                # exc_type, exc_obj, exc_tb = sys.exc_info()
                messages.append(traceback.format_exc())
            else:
                messages.append(u'Успешно')

    end = timezone.now()
    CronResult.objects.create(cron=cron,
                              start=start,
                              end=end,
                              text=u"Result: %s\n\nMessages: %s" % (result, u'\n'.join(messages)))

    return render(request, 'app_cron/run_cron.html',
                  {'messages': messages, 'time': (end - start).total_seconds(), 'result': result})
