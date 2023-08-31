# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

import its_utils.app_converter.functions as functions

from its_utils.app_get_params import get_params_from_sources


@login_required
@csrf_exempt
@get_params_from_sources
def csv_to_xls(request):

    return functions.xls_to_django_response(functions.csv_to_xls(request.its_params.get('csv', '')))
