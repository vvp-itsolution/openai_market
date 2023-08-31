# -*- coding: UTF-8 -*-

import json

from django.http import HttpResponse

from its_utils.functions2.get_apps import get_apps


def get_project_apps(request):

    if not request.user.is_superuser:
        return HttpResponse('Not authorized', status=400)

    return HttpResponse(json.dumps(get_apps()))
