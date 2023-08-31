# -*- coding: UTF-8 -*-

from django.shortcuts import render
from django.http import HttpResponse

from its_utils.app_get_params import get_params_from_sources


@get_params_from_sources
def model_detail(request, app, model_name):

    if not request.user.is_superuser:
        return HttpResponse('Not authorized', status=400)

    return render(request, 'app_model_view/model_detail.html', {'app': app,
                                                                'model': model_name})
