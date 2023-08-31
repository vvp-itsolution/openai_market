from django.http import HttpResponseForbidden
from django.shortcuts import redirect

from bitrix_utils.bitrix_auth.functions.bitrix_auth_required import bitrix_auth_required
from bitrix_utils.bitrix_telegram_log.models import PortalChat


@bitrix_auth_required()
def start_binding(request):
    if not request.bx_user.is_admin:
        return HttpResponseForbidden()

    portal_chat = PortalChat.get_for_portal(
        portal=request.bx_portal,
        app=request.bx_user_token.application,
    )

    return redirect(portal_chat.get_bind_url())
