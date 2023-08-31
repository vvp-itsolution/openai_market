# -*- coding: UTF-8 -*-

from django.shortcuts import render
from django.http import HttpResponse

from its_utils.app_get_params import get_params_from_sources
from its_utils.functions2.get_apps import get_apps
from its_utils.functions2.get_models import get_models


@get_params_from_sources
def model_list(request):

    if not request.user.is_superuser:
        return HttpResponse('Not authorized', status=400)

    apps_and_models = [
        {'name': app,
         'models': [m._meta.model_name for m in get_models(app)]}
        for app in get_apps()
    ]

    return render(request, 'app_model_view/model_list.html', {'apps': apps_and_models})
