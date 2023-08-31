# -*- coding: UTF-8 -*-

import json

from django.http import HttpResponse

from its_utils.app_get_params import get_params_from_sources
from its_utils.functions2.get_model import get_model


@get_params_from_sources
def get_model_fields_for_foreign(request):

    if not request.user.is_superuser:
        return HttpResponse('Not authorized', status=400)

    app_name = request.its_params.get('a')
    model_name = request.its_params.get('m')
    field_name = request.its_params.get('f')

    if not (app_name and model_name and field_name):
        return HttpResponse('Need app name, model name and field name', status=400)

    model = get_model(app_name, model_name)

    if not model:
        return HttpResponse('No model with name "%s" found for app "%s"' % (model_name, app_name), status=400)

    for field in model._meta.fields:
        if field.name == field_name:
            response = {
                'app': field.related_model._meta.app_label,
                'model': field.related_model._meta.model_name,
                'fields': [{'label': f.name, 'type': type(f).__name__} for f in field.related_model._meta.fields]
            }

            return HttpResponse(json.dumps(response))

    return HttpResponse('No field with name %s found for %s.%s model' % (field_name, model_name, app_name), status=400)
