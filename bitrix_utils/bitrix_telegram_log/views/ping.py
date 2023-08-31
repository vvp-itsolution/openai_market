from django.http import HttpResponse

from bitrix_utils.bitrix_auth.functions.bitrix_auth_required import bitrix_auth_required
from bitrix_utils.bitrix_telegram_log.models import PortalChat


@bitrix_auth_required()
def ping(request):
    portal_chat = PortalChat.get_for_portal(
        portal=request.bx_portal,
        app=request.bx_user_token.application,
    )

    if not portal_chat.chat:
        return HttpResponse('Чат не привязан')

    result = portal_chat.ping()
    return HttpResponse(result)
