# -*- coding: UTF-8 -*-

import json

from django.http import HttpResponse

from its_utils.functions2.get_apps import get_apps
from its_utils.functions2.get_models import get_models


def get_apps_and_models(request):

    if not request.user.is_superuser:
        return HttpResponse('Not authorized', status=400)

    apps_and_models = [
        {'app': app,
         'models': [m._meta.model_name for m in get_models(app)]}
        for app in get_apps()
    ]

    return HttpResponse(json.dumps(apps_and_models))
