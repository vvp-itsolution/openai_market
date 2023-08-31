# -*- coding: utf-8 -*-
from collections import namedtuple
from functools import wraps

import six
from django.conf import settings
from django.core.signing import BadSignature
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.encoding import force_str

try:
    import settings as project_settings
except ImportError:
    project_settings = None
from ..models import BitrixUserToken
from ._set_auth_cookie import set_auth_cookie


CheckCookieResult = namedtuple('CheckCookieResult',
                               ['bx_user_token', 'bx_user', 'set_cookie'])


def check_cookie_auth(request, application_names):
    """Проверяет авторизацию куками, возвращает токен, пользователя и set_cookie
    (при ``set_cookie == True`` авторизация прошла на самом деле не куками,
    а GET-параметром ``shs`` и для работы дальнейших переходов
    нужно установить куки авторизации).
    :type request: django.http.HttpRequest
    :type application_names: Iterable[str]
    :rtype: CheckCookieResult
    """
    bx_user_token, bx_user, set_cookie = None, None, False
    if request.GET.get('shs', 'nosecret') == settings.BITRIX_SHADOW_SECRET \
            and 'token_id' in request.GET:
        # Притворяемся пользователем.
        # Нужно проставить куки авторизации,
        # чтобы работали последующие переходы по страницам.
        set_cookie = True
        bx_user_token = BitrixUserToken.objects.get(pk=request.GET['token_id'])
        bx_user = bx_user_token.user
    else:
        request.bx_user = None
        for app in application_names:
            auth_cookie = 'b24app_auth_{}'.format(app)
            try:
                auth_token = request.get_signed_cookie(
                    auth_cookie,
                    salt=settings.SALT,
                    max_age=BitrixUserToken.AUTH_COOKIE_MAX_AGE,
                )
            except KeyError:
                # Если кука отсутствует - пробуем следующую
                continue
            except BadSignature:
                if request.COOKIES.get(auth_cookie, '').strip():
                    # Была передана неверно подписанная кука авторизации
                    raise
                # Если кука пустая, игнорируем - пробуем следующую
                continue

            bx_user_token = BitrixUserToken.get_by_token(auth_token)
            bx_user = bx_user_token.user

            if not bx_user_token.is_active and bx_user_token.refresh_error == BitrixUserToken.ERROR_OAUTH:
                # приложение удалено
                continue

            if request.bx_user is not None:
                break
    return CheckCookieResult(bx_user_token, bx_user, set_cookie)


def bad_sig_error(request, exception):
    its_logger = getattr(project_settings, 'ilogger', None)
    if its_logger is None:
        raise exception
    its_logger.exception(
        'bad-cookie-sig',
        u'auth failed due to bad signature: error {}; cookies {!r}'
        .format(force_str(str(exception)), request.COOKIES),
        exc_info=True,
    )
    return render(request, 'bitrix_auth/cookie_sig_error.html')


def bitrix_auth_required(*application_names):
    """Декоратор определяет, является ли user пользователем Bitrix.
    Куки устанавливаются декоратором bitrix_start_point
    """
    # if not application_names:
    #     raise TypeError('Expected at least 1 application name')

    its_logger = getattr(project_settings, 'ilogger', None)
    if its_logger is None:
        raise RuntimeError('No settings.ilogger')

    BITRIX_MODERATION_MODE = getattr(settings, 'BITRIX_MODERATION_MODE', False)

    def app_names():
        for item in application_names:
            if callable(item):
                item = item()
            if isinstance(item, six.string_types):
                yield item
            for app_name in item:
                yield app_name

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            try:
                application_names = list(app_names())
                if not application_names:
                    # В декораторе может быть не указан список приложений, а передан как ГЕТ параметр для общих вьюх
                    # Первое использование в лог телеграм боте
                    application_names.append(request.GET.get('app'))

                request.bx_user_token, request.bx_user, set_cookie = \
                        check_cookie_auth(request, application_names)

            except BadSignature as e:
                return bad_sig_error(request, e)
            except Exception as e:
                if BITRIX_MODERATION_MODE:
                    # Отдаем 200 ответ на время прохождения модерации
                    its_logger.error(
                        log_type='bitrix_auth_required %s' % type(e).__name__,
                        message=repr(e),
                    )
                    return HttpResponse('no auth')
                raise e
            if request.bx_user is None:
                return render(
                    request, 'bitrix_auth/cookie_error.html',

                    # Поменяли обратно на 401, так как в базе знаний есть проверка авторизации по статусу ответа
                    # https://b24.it-solution.ru/workgroups/group/17/tasks/task/view/7469/
                    status=200 if BITRIX_MODERATION_MODE else 401  # Было 401 но думаю 200 подойдет
                )

            request.bx_auth_token = \
                BitrixUserToken.get_auth_token(request.bx_user_token.id)
            request.user_token_sig = '{}::{}'.format(
                request.bx_user_token.id,
                request.bx_auth_token,
            )
            request.bx_portal = request.bx_user.portal
            try:
                response = func(request, *args, **kwargs)
                if set_cookie:
                    # Простановка кук (если притворились пользователем
                    # и для работы дальнейших переходов нужны установленные куки.)
                    user_token_sig = '{}::{}'.format(request.bx_user_token.id,
                                                     request.bx_auth_token)
                    response = set_auth_cookie(
                        response=response,
                        request=request,
                        user_token_sig=user_token_sig,
                        app_name=request.bx_user_token.application.name,
                    )
                return response
            except Exception as e:
                if BITRIX_MODERATION_MODE:
                    # Отдаем 200 ответ на время прохождения модерации
                    its_logger.error(
                        log_type='bitrix_auth_required %s' % type(e).__name__,
                        message=repr(e),
                    )
                    return HttpResponse('Internal server error')
                raise e
        return wrapper
    return decorator
