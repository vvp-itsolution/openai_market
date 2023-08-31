# -*- coding: UTF-8 -*-

import json
from django.core.serializers.json import DjangoJSONEncoder

from django.http import HttpResponse

from its_utils.app_get_params import get_params_from_sources
from its_utils.functions2.get_model import get_model


@get_params_from_sources
def get_model_data(request):

    if not request.user.is_superuser:
        return HttpResponse('Not authorized', status=400)

    app_name = request.its_params.get('a')
    model_name = request.its_params.get('m')
    fields = request.its_params.get('f')

    if not (app_name and model_name and fields):
        return HttpResponse('Need app name, model name and fields', status=400)

    model = get_model(app_name, model_name)

    if not model:
        return HttpResponse('No model with name "%s" found for app "%s"' % (app_name, model_name), status=400)

    data = model.objects.all().select_related().values(*fields.split(','))

    return HttpResponse(json.dumps(list(data), cls=DjangoJSONEncoder))
