# -*- coding: UTF-8 -*-

import json

from django.http import HttpResponse

from its_utils.app_get_params import get_params_from_sources
from its_utils.functions2.get_model import get_model


@get_params_from_sources
def get_model_fields(request):
    if not request.user.is_superuser:
        return HttpResponse('Not authorized', status=400)

    app_name = request.its_params.get('a')
    model_name = request.its_params.get('m')

    if not (app_name and model_name):
        return HttpResponse('Need app name and model name', status=400)

    model = get_model(app_name, model_name)

    if not model:
        return HttpResponse('No model with name "%s" found for app "%s"' % (model_name, app_name), status=400)

    response = {
        'model': model._meta.model_name,
        'app': app_name,
        'fields': [{'label': field.name, 'type': type(field).__name__}
                   for field in model._meta.fields],
    }

    return HttpResponse(json.dumps(response))
