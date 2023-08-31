# -*- coding: UTF-8 -*-

from django.http import HttpResponse
from django.shortcuts import render

from its_utils.app_cron.models import Cron


def cron_view(request, pk):

    if not request.user.is_superuser:
        return HttpResponse('Only superuser allowed', status=400)

    try:
        cron = Cron.objects.get(id=pk)
    except Cron.DoesNotExist:
        return HttpResponse('Cron with id %s was not found' % pk)

    return render(request, 'app_cron/cron_view.html', {'cron': cron})
