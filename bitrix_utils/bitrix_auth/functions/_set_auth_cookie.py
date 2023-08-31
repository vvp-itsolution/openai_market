# -*- coding: utf-8 -*-
import django
from django.conf import settings
from six.moves.http_cookies import CookieError

from ..models import BitrixUserToken


def set_auth_cookie(response, request, user_token_sig=None, app_name=None):
    app_name = app_name or request.bitrix_app.name
    cookie_template = 'b24app_auth_{}'
    # Удаление прочих кукизов
    app_codes = set(getattr(settings, 'BITRIX_APP_CODES', []))
    for app_code in app_codes:
        if app_name == app_code:
            continue
        response.delete_cookie(cookie_template.format(app_code))
    # Установка куки авторизации
    cookie_key = cookie_template.format(app_name)

    # Secure + SameSite=None необходимо для новых версий Chrome
    # A cookie associated with a cross-site resource at
    # http://articles.it-solution.ru/ was set without the SameSite attribute.
    # It has been blocked, as Chrome now only delivers cookies with cross-site
    # requests if they are set with SameSite=None and Secure. You can review
    # cookies in developer tools under Application>Storage>Cookies and see more
    # details at https://www.chromestatus.com/feature/5088147346030592 and
    # https://www.chromestatus.com/feature/5633521622188032.
    # samesite_kwargs = {}
    # if django.get_version() >= '3':
    #     # https://github.com/django/django/pull/11894
    #     samesite_kwargs['samesite'] = 'none'

    response.set_signed_cookie(
        cookie_key,
        user_token_sig or request.user_token_sig,
        salt=settings.SALT,
        max_age=BitrixUserToken.AUTH_COOKIE_MAX_AGE,

        # required for chrome
        secure=True,
    )
    try:
        response.cookies[cookie_key]['samesite'] = 'None'  # hack
    except CookieError:
        # https://stackoverflow.com/a/50813092/2468136
        response.cookies[cookie_key]._reserved['samesite'] = 'None'

    return response
