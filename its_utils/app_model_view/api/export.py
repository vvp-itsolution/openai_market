# -*- coding: UTF-8 -*-

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from its_utils.app_converter.functions import query_to_xls, xls_to_django_response

from its_utils.app_get_params import get_params_from_sources
from its_utils.functions2.get_model import get_model


@csrf_exempt
@get_params_from_sources
def export(request):

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

    return xls_to_django_response(query_to_xls(model, fields=fields.split(',')))
