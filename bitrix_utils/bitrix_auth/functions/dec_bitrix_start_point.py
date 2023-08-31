# -*- coding: utf-8 -*-
from functools import wraps
from pprint import pformat

import six
import json
from six.moves import urllib_parse
import threading
import requests

from django.conf import settings
from django.http import QueryDict, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError

from settings import ilogger
from integration_utils.bitrix24.functions.api_call import BitrixTimeout, ConnectionToBitrixError
from integration_utils.bitrix24.functions.batch_api_call import BatchApiCallError, JsonDecodeBatchFailed
from ..functions._set_auth_cookie import set_auth_cookie
from ..models import (
    BitrixApp,
    BitrixPortal,
    BitrixUser,
    BitrixUserToken,
    BitrixAppInstallation,
)
from ..models.bitrix_user_token import BitrixApiError

if False:
    from typing import Tuple, Sequence, Optional, Any, Callable


BITRIX_AUTH_SERVER = 'https://oauth.bitrix.info'
START_POINT_REQUESTS_TIMEOUT = 15


@six.python_2_unicode_compatible
class EnterFromBitrix(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

    def render_response(self, request, status=200):
        return render(request, 'bitrix_auth/bitrix_start_point_exception.html',
                      dict(exc=self.message), status=status)


class AuthRedirect(EnterFromBitrix):
    def __init__(self, portal_domain, app_id, https=True, request=None):
        """
        :param portal_domain: Домен битрикс-портала
        :param app_id: ID приложения на данном портале (из app.info)
        """
        next = '/marketplace/app/%d/' % int(app_id)
        redirect_to = '{protocol}://{domain}/auth?{query}'.format(
            protocol='https' if https else 'http',
            domain=portal_domain,
            query=urllib_parse.urlencode(dict(backurl=next))
        )
        self.response = render(
            request=request,
            template_name='bitrix_auth/fullscreen_redirect.html',
            context=dict(
                url=redirect_to,
                message='Авторизация...',
            ),
        )
        self.message = 'redirect to %s' % redirect_to

    def render_response(self, request, status=200):
        self.response.status_code = status
        return self.response

    @classmethod
    def for_member(cls, member_id, portal_domain, https=True, app_code=None,
                   request=None):
        tokens = BitrixUserToken.objects.filter(
            is_active=True,
            user__portal__member_id=member_id,
        )
        if app_code:
            tokens = tokens.filter(application__name=app_code)
        # Не факт, что токен от нужного приложения, но чем богаты, тем и рады
        token = tokens.first()
        if token is None:
            return None
        app_id = token.call_api_method(
            'app.info',
            timeout=START_POINT_REQUESTS_TIMEOUT,
        )['result']['ID']
        return cls(portal_domain, app_id, https=https, request=request)


@six.python_2_unicode_compatible
class AuthCheckError(Exception):
    def __init__(
            self,
            auth_token,
            expected_client_ids,
            actual_client_id,
            reason=None,
    ):
        # type: (str, Sequence[str], Optional[str], Optional[Any]) -> None
        self.auth_token = auth_token
        self.expected_client_ids = expected_client_ids
        self.actual_client_id = actual_client_id
        self.reason = reason

    def __str__(self):
        return '[auth: {self.auth_token}]\n' \
               'expected client_id: {self.expected_client_ids!r}\n' \
               'got: {self.actual_client_id!r} ' \
               'reason: {self.reason!r}' \
               .format(self=self)

    def __repr__(self):
        rv = '<{} {!s}>'.format(type(self).__name__, self)
        return rv.encode('utf8') if six.PY2 else rv


def bitrix_start_point_process(settings_name, request, credentials=None, *args, **kwargs):
    """
    Точка входа в приложение.
    Если нет токена, зачит в приложение зашли не через Битрикс
    В сессию сохраняются:
        auth - токен пользователя,
        refresh - токен для обновления токена пользователя
        portal - URL портала, откуда пришел запрос
        member_id - идентификатор этого портала
    """

    if (args or kwargs) and settings.DEBUG:
        # args и kwargs у функции не используются,
        # возможно это какое-то древнее легаси.
        # Пока пусть будет ошибка при локальном запуске,
        # если вылезет на каком-нибудь старом проекте - будет шанс поправить.
        raise RuntimeError('unexpected arguments: '
                           'args={args!r}, kwargs={kwargs!r}'
                           .format(**locals()))

    # На всякий случай будет логироваться время работы этого декоратора.
    # Вдруг окажется что все эти запросы и обновления происходят слишком медленно?
    start = timezone.now()
    app_sid = auth_token = refresh_token = domain = member_id = None

    # Эта информация приходит от битрикса
    if credentials:
        # "Ручной" вызов процесса для OAuth 2.0
        auth_token = credentials.get('access_token')
        refresh_token = credentials.get('refresh_token')
        member_id = credentials.get('member_id')
        domain = credentials.get('domain')
    elif request.GET.get('shs', 'nosecret') == settings.BITRIX_SHADOW_SECRET and request.GET.get('token_id', None):
        # Это если хотим прикнуться пользователем
        sh_but = BitrixUserToken.objects.get(pk=request.GET.get('token_id', None))
        sh_but.refresh()
        auth_token = sh_but.auth_token
        refresh_token = sh_but.refresh_token
        # Надо ли проверять при входе через секрет? Пока наверное нет
        member_id = sh_but.user.portal.member_id
        domain = sh_but.user.portal.domain
    elif request.POST.get('auth[access_token]'):
        # Похоже что это сделано для ЧатБотов FIXME
        auth_token = request.POST.get('auth[access_token]')
        refresh_token = request.POST.get('auth[refresh_token]')
    elif 'AUTH_ID' in request.POST:
        # Это для входа через IFRAME
        auth_token = request.POST.get('AUTH_ID')
        refresh_token = request.POST.get('REFRESH_ID')
        app_sid = request.GET.get('APP_SID')
        https = request.GET.get('PROTOCOL', '1') == '1'
        if (
            request.GET.get('member_id') and
            request.GET.get('DOMAIN') and
            not auth_token
        ):
            # Коробки со слетевшей авторизацией
            # https://ts.it-solution.ru/#/ticket/53082/

            #TODO Думаю это уже не нужно, т.к уже паролем закрыт вход.
            ilogger.warning("without_auth_token", "а попадает ли еще сюда?")

            try:
                redirect = AuthRedirect.for_member(
                    member_id=request.GET['member_id'],
                    portal_domain=request.GET['DOMAIN'],
                    https=https,
                    app_code=settings_name,
                    request=request,
                )
            except (BitrixTimeout, BitrixApiError):
                raise EnterFromBitrix('Сервер Битрикс24 недоступен')
            else:
                raise redirect

    # Получение member_id и домена от oauth-сервера Б24
    if member_id is None and auth_token:
        try:
            domain, member_id = get_portal_domain_and_member_id(auth_token)
        except AuthCheckError as e:
            ilogger.error('auth_check_error', repr(e))
            raise EnterFromBitrix(
                'Сервер авторизации Б24 не подтвердил данные авторизации. '
                'Попробуйте обновить страницу.')

    if not auth_token:
        get_post_params = '{}\n\nGET: {}\n\nPOST: {}'.format(request.path, request.GET, request.POST)

        if not credentials and not request.GET and not request.POST:
            # Если никаких данных не передано, то это кто-то типа поискового бота стучится
            ilogger.debug(u'failed_attempt_to_enter_empty', 'Пустые Гет Пост и Прочее наверное поисковый бот стучится')

        # Если что-то есть, то логируем
        else:
            ilogger.error(
                u'failed_attempt_to_enter=> {}'.format(get_post_params)
            )

        raise EnterFromBitrix('Неверные параметры запроса: {}'.format(get_post_params))

    request.bx_user_is_new = None
    request.bx_auth_key = None
    request.bx_user = None

    _log_mess = 'start_point_auth_info=>auth_token: {}, refresh_token: {}, domain: {}, member_id: {}'.format(
        auth_token, refresh_token, domain, member_id)
    ilogger.debug(_log_mess)

    if not all((auth_token, domain, member_id)):
        raise EnterFromBitrix('Неверные параметры авторизации (auth_token, domain, member_id): {}'.format(
            (auth_token, domain, member_id)
        ))

    # Запрашиваем всю информацию о пользователе и портале
    # Иногда, приложению будет не хватать прав на запрос, например, групп
    # Тогда надо просто игнорировать эту информацию и попытаться записать все что можно
    # Минимум, который нужен - это информация о пользователе
    methods = [
        ('user_info', 'user.current', None),
        ('admin_info', 'user.admin', None),
        ('user_groups', 'sonet_group.user.groups', None),
        ('app_info', 'app.info', None),
    ]

    try:
        dynamic_token = BitrixUserToken(auth_token=auth_token, domain=domain)
        batch_response = dynamic_token.batch_api_call_v3(
            methods,
            timeout=START_POINT_REQUESTS_TIMEOUT,
        )
    except BitrixTimeout:
        raise EnterFromBitrix('Сервер Битрикс24 %s недоступен' % domain)
    except BitrixApiError as e:
        ilogger.error(u'failed_attempt_to_enter', pformat(e))
        raise EnterFromBitrix('Не удалось получить информацию о пользователе')
    except BatchApiCallError as e:
        ilogger.error(u'failed_attempt_to_enter_{}'.format(e.reason), pformat(e))
        raise EnterFromBitrix('Не удалось получить информацию о пользователе')
    except ConnectionToBitrixError as e:
        ilogger.error(u'failed_attempt_to_enter_connection_error', pformat(e))
        raise EnterFromBitrix('Портал не отвечает по https. Проверьте ssl сертификат или файерволл')
    except JsonDecodeBatchFailed as e:
        ilogger.error(u'failed_attempt_to_enter_JsonDecodeBatchFailed', pformat(e))
        raise EnterFromBitrix('Батч возвращает не json проверьте rest api')


    user_info = batch_response['user_info']['result']
    admin_info = batch_response['admin_info']['result']
    app_info = batch_response['app_info']['result']

    # Если не удалось получить user_info - значит что-то не так
    if user_info is None or admin_info is None or app_info is None:
        ilogger.error(u'failed_attempt_to_enter=>%s' % batch_response)
        raise EnterFromBitrix('Не удалось получить информацию о пользователе')

    app_code = app_info.get('CODE')
    try:
        bitrix_app = BitrixApp.objects.get(name=app_code)
    except BitrixApp.DoesNotExist:
        ilogger.error(u'bitrix_app_code_not_found=> {}'.format(app_code))
        if settings_name:
            bitrix_app = BitrixApp.objects.get(name=settings_name)
            app_code = settings_name

        else:
            raise

    # Есть информация о пользователе - можно продолжить

    # member_id - уникальный id портала
    # https://dev.1c-bitrix.ru/learning/course/?COURSE_ID=43&LESSON_ID=4997
    portal, portal_created = BitrixPortal.objects.get_or_create(member_id=member_id)
    portal.domain = domain
    now = timezone.now()

    # Пока получаем информацию о пользователе, может прийти новый запрос от того же пользователя
    user, user_created = BitrixUser.objects.get_or_create(portal=portal, bitrix_id=int(user_info['ID']))

    # Обновить основную информацию о пользователе
    user.update_from_bx_response(user=user_info, save=False)

    # Обновление прочих полей пользователя
    user.is_admin = admin_info  # админ ли юзер?
    user.user_is_active = True  # если дошел до сюда - точно активный

    # UPDATED 10.10.19 bvv:
    # похоже это осталось с тех времен, когда токены хранились прямо
    # в таблице пользователей
    # user.auth_token_date = now

    # NB! sonet_group.user.groups возвращает больше 50 групп при вызове батч-запросом,
    # проверено на облачном портале, у пользователя было 55 групп.
    user_groups = batch_response['user_groups']['result']
    if user_groups is not None:
        # Записать в каких группах состоит пользователь
        user.group_ids = [group['GROUP_ID'] for group in user_groups]

    # Указать что портал активен и сохранить его и пользователя
    # Сохранять нужно после отделений,
    # потому что там могли создаться отделы, в которые входит пользователь
    portal.active = True
    portal.save()

    # Простое Джанго сохранение, взамен save в BitrixUser,
    # чтобы не было апдейта токена
    # UPDATED 10.10.19 bvv:
    # похоже это осталось с тех времен, когда токены хранились прямо
    # в таблице пользователей, танцы с super(BitrixUser, user)
    # более не влияют на обновление токена.
    super(BitrixUser, user).save()

    # Получение или инициализация токена из БД
    try:
        bitrix_user_token, _ = BitrixUserToken.objects.get_or_create(application=bitrix_app, user=user,
                                                                     defaults={'auth_token_date': timezone.now()})
    except IntegrityError:
        bitrix_user_token = BitrixUserToken.objects.get(application=bitrix_app, user=user)

    # Заполнение полей токена
    bitrix_user_token.user = user
    bitrix_user_token.auth_token = auth_token

    if refresh_token:
        bitrix_user_token.refresh_token = refresh_token

    elif not user.id:
        # т. к. для refresh_token is_null=False, присвоим пустую строку новому токену
        bitrix_user_token.refresh_token = ''

    bitrix_user_token.auth_token_date = now
    bitrix_user_token.is_active = True
    bitrix_user_token.refresh_error = 0
    bitrix_user_token.application = bitrix_app
    if app_sid is not None:
        bitrix_user_token.app_sid = app_sid
    bitrix_user_token.save()

    # Простое Джанго сохранение, взамен save в BitrixUser, чтобы не было апдейта токена
    super(BitrixUser, user).save()

    # Информацию о пользователе и портале записать в объект request
    # Она будет использована в функциях, у которых есть данный декоратор
    request.bx_user = user
    request.bx_portal = portal
    request.bx_user_is_new = user_created
    request.bx_portal_is_new = portal_created
    request.bx_user_token = bitrix_user_token
    request.bx_auth_token = BitrixUserToken.get_auth_token(bitrix_user_token.id)
    request.bitrix_app = bitrix_app
    request.user_token_sig = '{}::{}'.format(bitrix_user_token.id, request.bx_auth_token)

    # Параметры, переданные в заголовке Referer
    request.bx_referer_params = QueryDict('', mutable=True)

    placement_options = request.POST.get('PLACEMENT_OPTIONS')
    http_referer = request.META.get('HTTP_REFERER')

    if placement_options and placement_options.strip('"') != 'undefined':
        try:
            request.bx_referer_params.update(json.loads(placement_options))
        except Exception as e:
            ilogger.error('placement_parse_error', 'placement_parse_error')

    elif http_referer:
        request.bx_referer_params = QueryDict(urllib_parse.urlparse(http_referer).query)

    try:
        app_installation, _ = BitrixAppInstallation.objects.get_or_create(
            portal=portal, application=bitrix_app
        )
        app_installation.app_id = app_info.get('ID')
        app_installation.save()
    except:
        ilogger.exception('app_info_id=>app_info.get(ID)')

    # регистрация запусков приложения
    try:
        _start_in_thread(
            register_application_run,
            bitrix_id=user.bitrix_id,
            client_id=bitrix_app.bitrix_client_id,
            member_id=member_id,
            domain=domain,
            app_name=app_code,
            first_name=user_info.get('NAME', ''),
            last_name=user_info.get('LAST_NAME', ''),
            email=user_info.get('EMAIL', ''),
            skype=user_info.get('UF_SKYPE', ''),
            work_phone=user_info.get('WORK_PHONE', ''),
            personal_mobile=user_info.get('PERSONAL_MOBILE', ''),
        )
    except Exception as e:
        ilogger.error(u'register_application_run=>got an exception: {error}'.format(error=e))

    ilogger.info(u'bitrix_start_point_working_time=>%s' % (timezone.now() - start).total_seconds())
    return True


def _start_in_thread(f, *args, **kwargs):
    # type: (Callable, Any, Any) -> threading.Thread
    thread = threading.Thread(target=f, args=args, kwargs=kwargs)
    thread.start()
    return thread


def register_application_run(bitrix_id, client_id, member_id, domain, **kwargs):
    """
    делает запрос на урл, на котором регистрируется запуск приложения (создается запись в БД)
    kwargs принимает информацию о пользователе first_name, last_name, email, skype, work_phone, personal_mobile, app_name
    """
    params = {'bitrix_id': bitrix_id,
              'client_id': client_id,
              'member_id': member_id,
              'domain': domain}
    params.update(kwargs)
    url = 'http://rootapp.it-solution.ru/register_application_run/'
    try:
        response = requests.get(url, params, timeout=5)
        if response.status_code != 200:
            ilogger.warning('rootapp_register_application_run_fail', 'return code %s' % response.status_code, exc_info=True)

    except Exception as e:
        ilogger.error('rootapp_register_application_run_error', repr(e))


def get_portal_domain_and_member_id(auth_token, valid_client_ids=None):
    # type: (str, Optional[Sequence[str]]) -> Tuple[str, str]
    """Получает domain и member_id oauth.bitrix.info

    Так как приложения могу работать с коробками, то нам необходимо
    удостовериться, что переданный токен настоящий,
    а member_id и domain не поддельные.

    :param auth_token: переданный приложению авторизационный токен
    :param valid_client_ids: подходящие client_id, по умолчанию:
        bitrix_client_id всех BitrixApp в БД

    :returns: Пара домен и member_id: ('domain.bitrix24.ru', '88234...')
    :raises: AuthCheckError:
        - сервер авторизации не вернул ответ, не вернул json
        - неверный авторизационный токен
        - несовпадение client_id приложения и данных oauth.bitrix.info
    """
    if valid_client_ids is None:
        valid_client_ids = set(
            BitrixApp.objects.values_list('bitrix_client_id', flat=True))

    try:
        http_response = requests.get(
            BITRIX_AUTH_SERVER + '/rest/app.info',
            dict(auth=auth_token),
            timeout=START_POINT_REQUESTS_TIMEOUT,
        )
        response = http_response.json()
    except requests.Timeout:
        raise EnterFromBitrix('Сервер авторизации Битрикс24 недоступен')
    except ValueError as e:
        raise AuthCheckError(
            auth_token=auth_token,
            expected_client_ids=valid_client_ids,
            actual_client_id=None,
            reason=http_response.text,
        )
    except requests.RequestException as e:
        raise AuthCheckError(
            auth_token=auth_token,
            expected_client_ids=valid_client_ids,
            actual_client_id=None,
            reason=e,
        )

    if 'result' not in response:
        raise AuthCheckError(
            auth_token=auth_token,
            expected_client_ids=valid_client_ids,
            actual_client_id=None,
            reason=response,
        )

    try:
        client_id = response['result']['client_id']
        domain = response['result']['install']['domain']
        member_id = response['result']['install']['member_id']
    except KeyError:
        raise AuthCheckError(
            auth_token=auth_token,
            expected_client_ids=valid_client_ids,
            actual_client_id=None,
            reason=response,
        )

    if client_id not in valid_client_ids:
        raise AuthCheckError(
            auth_token=auth_token,
            expected_client_ids=valid_client_ids,
            actual_client_id=client_id,
            reason=response,
        )

    return domain, member_id


def get_response(response):
    """Проблема: https://vendors.bitrix24.ru при добавлении новой версии
    требует 200 ответа.

    Решение: при установке в settings.py BITRIX_MODERATION_MODE
    отдаем 200 ответ, вместо 4xx-5xx ответов.
    """
    if getattr(settings, 'BITRIX_MODERATION_MODE', False) and \
            response.status_code >= 400:
        response.status_code = 200

    return response


def bitrix_start_point(settings_name=None, iphone_redis_pickle_dance=False):
    """Задекорированная декоратором вьюха может использоваться
    как точка встраивания приложения в Битрикс24.
    :param settings_name: Название приложения (как в Битриксе)
        (если не указано - берется из запроса к app.info - параметр CODE)
    :param iphone_redis_pickle_dance: removed
    """

    if iphone_redis_pickle_dance and settings.DEBUG:
        raise Exception('iphone_redis_pickle_dance is removed')

    def inner_bitrix_start_point(func):
        @csrf_exempt
        @xframe_options_exempt
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            err_message = 'No auth'
            try:
                # Основная процедура авторизации
                bitrix_start_point_process(settings_name=settings_name,
                                           request=request)
                err_message = 'Internal server error'
                response = func(request, *args, **kwargs)
                response = set_auth_cookie(response, request)
            except AuthRedirect as e:
                return e.response
            except EnterFromBitrix as e:
                return e.render_response(request)
            except Exception as e:
                if getattr(settings, 'BITRIX_MODERATION_MODE', False):
                    # Отдаем 200 ответ на время прохождения модерации
                    ilogger.error(
                        log_type='bitrix_start_point %s' % type(e).__name__,
                        message=repr(e),
                    )
                    return HttpResponse(err_message)
                raise e
            return get_response(response)
        return wrapper
    return inner_bitrix_start_point
