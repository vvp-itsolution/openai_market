# coding=utf-8
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from bitrix_utils.bitrix_auth.functions.bitrix_user_required import bitrix_user_required
from its_utils.app_get_params import get_params_from_sources


@csrf_exempt
@get_params_from_sources
@bitrix_user_required
def set_crm_event_bindings(request):
    """
    Подписаться или отписаться от подписок на события
    """

    state = request.its_params.get('state')

    settings, _ = PortalSettings.objects.get_or_create(portal=request.bx_user.portal)
    if state:
        settings.unsubscribe_from_excluded_events()
        settings.subscribe_on_events()
    else:
        settings.unsubscribe_from_events()

    return JsonResponse({'success': True})
