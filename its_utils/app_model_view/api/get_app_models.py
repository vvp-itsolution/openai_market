# -*- coding: UTF-8 -*-

import json

from django.http import HttpResponse

from its_utils.app_get_params import get_params_from_sources
from its_utils.functions2.get_models import get_models


@get_params_from_sources
def get_app_models(request):

    if not request.user.is_superuser:
        return HttpResponse('Not authorized', status=400)

    app_name = request.its_params.get('a')

    if not app_name:
        return HttpResponse('Need app name and model name', status=400)

    models = get_models(app_name)

    return HttpResponse(json.dumps([m._meta.model_name for m in models]))
