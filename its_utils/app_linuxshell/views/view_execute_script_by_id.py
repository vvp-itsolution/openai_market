# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import permission_required
from its_utils.app_linuxshell.models import Script


def view_execute_script_by_id(request, script_id):
    output = Script.objects.get(pk=script_id).execute()

    return HttpResponse(output)