# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import permission_required
from its_utils.app_linuxshell.models import Script



@csrf_exempt
@require_POST
@permission_required('is_superuser')
def execute_script_view(request):
    script_id = request.POST.get('script_id', 0)
    output = Script.objects.get(pk=script_id).execute()

    return HttpResponse(output)