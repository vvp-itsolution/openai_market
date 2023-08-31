# -*- coding: UTF-8 -*-

import hashlib
import six
import sys
import traceback
import requests

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from django.utils import timezone

from bitrix_utils.bitrix_auth.exceptions import BitrixApiError
from integration_utils.bitrix24.functions.api_call import (
    api_call,
    ConnectionToBitrixError,
    DEFAULT_TIMEOUT,
    BitrixTimeout,
)

from integration_utils.bitrix24.functions.batch_api_call import _batch_api_call, BatchApiCallError
from its_utils.app_admin.get_admin_url import get_admin_url, get_admin_a_tag
from its_utils.app_logger.its_logger.mute_logger import MuteLogger
from settings import ilogger


if False:
    from typing import Optional, Sequence, Iterable, Any

from its_utils.functions.compatibility import get_json_field

JSONField = get_json_field()

PYTHON_VERSION = sys.version_info.major
STRING_TYPES = six.string_types
INTEGER_TYPES = six.integer_types


def refresh_all():
    return BitrixUserToken.refresh_all()



class BitrixTokenRefreshError(BitrixApiError):
    pass

class BitrixApiServerError(BitrixApiError):
    is_internal_server_error = True

class SnapiError(BitrixApiError):
    pass


def validate_bitrix_request(value):
    if value is None:
        return

    if type(value) is not list or len(value) != 2 or not (
                isinstance(value[0], STRING_TYPES) and isinstance(value[1], dict)
    ):
        raise ValidationError(
            u'Notation is ["crm.deal.list", {"filter": {"STAGE_ID": "NEW"}}].'
        )


class BitrixUserToken(models.Model):
    EXPIRED_TOKEN = 2
    INVALID_GRANT = 3
    NOT_INSTALLED = 4
    PAYMENT_REQUIRED = 5
    PORTAL_DELETED = 10
    ERROR_CORE = 11
    ERROR_OAUTH = 12
    ERROR_403_or_404 = 13
    NO_AUTH_FOUND = 14
    AUTHORIZATION_ERROR = 15
    ACCESS_DENIED = 16
    APPLICATION_NOT_FOUND = 17
    INVALID_TOKEN = 18
    USER_ACCESS_ERROR = 18

    REFRESH_ERRORS = (
        (0, 'Нет ошибки'),
        (1, 'Не установлен портал (Wrong client)'),
        (EXPIRED_TOKEN, 'Устарел ключ совсем (Expired token)'),
        # бывает если ключи прилжения неправильные и "ВОЗМОЖНО" когда уже совсем протух токен
        (INVALID_GRANT, 'Инвалид грант (Invalid grant)'),
        (NOT_INSTALLED, 'Не установлен портал (NOT_INSTALLED)'),
        (PAYMENT_REQUIRED, 'Не оплачено (PAYMENT_REQUIRED)'),
        (6, 'Домен отключен или не существует'),
        (8, 'ошибка >= 500 '),
        (9, 'Надо разобраться (Unknown Error)'),
        (PORTAL_DELETED, 'PORTAL_DELETED'),
        (ERROR_CORE, 'ERROR_CORE'),
        (ERROR_OAUTH, 'ERROR_OAUTH'),
        (ERROR_403_or_404, 'ERROR_403_or_404'),
        (NO_AUTH_FOUND, 'NO_AUTH_FOUND'),
        (AUTHORIZATION_ERROR, 'AUTHORIZATION_ERROR'),
        (ACCESS_DENIED, 'ACCESS_DENIED'),
        (APPLICATION_NOT_FOUND, 'APPLICATION_NOT_FOUND'),
        (INVALID_TOKEN, 'INVALID_TOKEN'),
        (USER_ACCESS_ERROR, 'USER_ACCESS_ERROR'),
    )

    AUTH_COOKIE_MAX_AGE = None   # as long as the client’s browser session

    SNAPI_URL = 'https://snapi.it-solution.ru/api/'

    user = models.ForeignKey('bitrix_auth.BitrixUser', related_name='bitrix_user_token', on_delete=models.CASCADE)

    auth_token = models.CharField(max_length=70)
    refresh_token = models.CharField(max_length=70, default='', blank=True)
    auth_token_date = models.DateTimeField()
    app_sid = models.CharField(max_length=70, blank=True)

    is_active = models.BooleanField(default=True)
    refresh_error = models.PositiveSmallIntegerField(default=0, choices=REFRESH_ERRORS)

    application = models.ForeignKey('bitrix_auth.BitrixApp', null=True, on_delete=models.CASCADE)
    bitrix_request = JSONField(null=True, blank=True, validators=[validate_bitrix_request],
                               help_text='Example: ["crm.deal.list", {"filter": {"STAGE_ID": "NEW"}}]')

    bitrix_response = JSONField(null=True, blank=True)
    process_bitrix_request = models.BooleanField(default=False)

    class Meta:
        app_label = 'bitrix_auth'
        unique_together = (("application", "user"),)

    @property
    def domain(self):
        return self._domain or self.user.portal.domain

    @domain.setter
    def domain(self, value):
        self._domain = value

    def __init__(self, *args, domain=None, web_hook_auth=None, **kwargs):
        # 1) Можут в БД лежать уже готовые токены и тогда просто их используем
        # 2) Если надо на лету делать токены для вызовов методов АПИ, то
        # BitrixUserToken(auth_token='65c09d5d001c767d002443c00000000100000301144', domain='b24.it-solution.ru')
        # 3) Можно на лету собрать вебхук токен
        # BitrixUserToken(web_hook_auth='1/ywefwefj38fjifiewfe', domain='b24.it-solution.ru')
        # TODO переделать это каогда либо
        # Пример как с нуля писать не надо
        # Для того чтобы не накосячить при рефаторинге функции call_api_method
        # web_hook_auth = '1/ywefwefj38fjifiewfe'
        self._domain = domain
        self.web_hook_auth = web_hook_auth
        super().__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.process_bitrix_request:
            self.do_process_bitrix_request()

        return super(BitrixUserToken, self).save(*args, **kwargs)

    def do_process_bitrix_request(self):
        if self.process_bitrix_request and self.bitrix_request:
            try:
                validate_bitrix_request(self.bitrix_request)

            except ValidationError:
                self.bitrix_response = None
                ilogger.warning(
                    u'bitrix_user_token_process_request',
                    u'invalid bitrix_request - id{}'.format(self.id)
                )

            else:
                method, params = self.bitrix_request
                try:
                    response = self.call_api_method(method, params.copy())
                    self.bitrix_response = response
                except BitrixApiError as e:
                    self.bitrix_response = e



        self.process_bitrix_request = False

    def user_token_sig(self):
        return self.id and '{}::{}'.format(self.id, self.get_auth_key())

    @classmethod
    def get_auth_token(cls, pk):
        return hashlib.md5('{}_token_{}'.format(pk, settings.SALT).encode()).hexdigest()

    def get_auth_key(self):
        return BitrixUserToken.get_auth_token(self.pk)

    @classmethod
    def get_by_token(cls, token):
        # Используется в декораторе bitrix_user_required для пользователиских АПИ запросов из приложений
        pk = cls.check_token(token)
        if pk:
            return cls.objects.get(pk=pk)

    @classmethod
    def check_token(cls, token):
        pk, token = token.split('::')
        # except (AttributeError, ValueError):
        #     return
        if token == cls.get_auth_token(pk):
            return pk

    @classmethod
    def get_random_token(cls, application_name, portal_id, is_admin=True, using=None):
        # type: (str, int, Optional[bool], Optional[str]) -> BitrixUserToken
        """
        Получить один любой активный токен

        :param application_name: имя приложения для которого необходим токен (строка)
        :param portal_id: <BitrixPortal foo.bitrix24.ru>.id
        :param is_admin: токен должен иметь права администратора?

        :raise BitrixUserTokenDoesNotExist: если запрошенного токена не существует
        :return: BitrixUserToken instance
        """

        return cls.get_random_token_for_apps(
            application_names=[application_name],
            portal_id=portal_id,
            is_admin=is_admin,
            using=using,
        )

    @classmethod
    def get_random_token_for_apps(cls, application_names, portal_id,
                                  is_admin=True, using=None):
        # type: (Sequence[str], int, Optional[bool], Optional[str]) -> BitrixUserToken
        """Получить один любой активный токен любого из переданных приложений

        :param application_names: имена приложений (список строк)
        :param portal_id: <BitrixPortal foo.bitrix24.ru>.id
        :param is_admin: токен должен иметь права администратора?
            None - не важно (админский при наличии активного, иначе простого юзера)
        :param using: for <QuerySet>.using(using)
        """

        if not application_names:
            from bitrix_utils.bitrix_auth.models import BitrixApp
            bxapps = list(BitrixApp.objects.all().values_list("name", flat=True))
            ilogger.debug("set_app_names", "app names required application_names={}".format(bxapps))
            assert application_names

        objects = cls.objects.using(using) if using else cls.objects
        tokens = objects.filter(
            application__name__in=application_names,
            user__portal_id=portal_id,
            is_active=True,
        )

        if is_admin:
            tokens = tokens.filter(user__is_admin=is_admin)
        else:
            tokens = tokens.order_by('-user__is_admin')
        token = tokens.defer('app_sid').first()  # TODO defer убрать когда нибудь

        if token is None:
            raise BitrixUserTokenDoesNotExist(
                'application_name: {}, portal_id: {}'
                .format(application_names, portal_id)
            )

        if is_admin:
            token.user.update_is_admin(token)
            if not token.user.is_admin:
                return cls.get_random_token_for_apps(application_names, portal_id, is_admin=is_admin, using=using)

        return token

    def upgrade_to_admin(self, application_names=None, portal_id=None,
                         using=None):
        # type: (Optional[Sequence[str]], Optional[int], Optional[str]) -> BitrixUserToken
        """При вызове с админским токеном - возвращает его же,
        при вызове с не-админским - достает и отдает админский.

        Если application_names или portal_id пусты - берутся от текущего токена
        """
        return self if self.user.is_admin else self.get_random_token_for_apps(
            application_names=application_names or [self.application.name],
            portal_id=portal_id or self.user.portal_id,
            is_admin=True,
            using=using,
        )

    def refresh(self, timeout=DEFAULT_TIMEOUT, v=1):
        """
        Если успешно обновился токен, то возвращаем True
        Если что-то пошло не так то False

        :param timeout: таймаут запроса
        """
        if not self.pk:
            # Динамический токен
            raise BitrixTokenRefreshError(True, dict(error='expired_token'), 401, "cant_refresh")

        if self.application.is_webhook:
            # Нельзя обновлять вебхуки
            if v == 2:
                raise BitrixTokenRefreshError(True, dict(error='webhook refresh?'), 401, "webhook_refresh")
            return False

        params = {
            'grant_type': 'refresh_token',
            'client_id': self.application.bitrix_client_id,
            'client_secret': self.application.bitrix_client_secret,
            'refresh_token': self.refresh_token,
        }
        params = '&'.join(['%s=%s' % (k, v) for k, v in params.items()])
        url = 'https://oauth.bitrix.info/oauth/token/?{}'.format(params)
        # url = 'https://{}/oauth/token/?{}'.format(self.user.portal.domain, params)
        try:
            response = requests.get(url, timeout=timeout)
        except requests.Timeout as e:
            raise BitrixTimeout(requests_timeout=e, timeout=timeout)


        if response.status_code >= 500:
            ilogger.warning(u'refresh_token_error_gt500',
                            u'{} {} -> {}'.format(url, params, response.text))
            self.refresh_error = 8
            # self.is_active = False
            # self.save()
            if v == 2:
                raise BitrixTokenRefreshError(True, dict(error='refresh_token_error_gt500?'), 401, "refresh_token_error_gt500")
            return False


        try:
            response_json = response.json()
        except (ValueError, TypeError):
            if response.status_code >= 403 and "portal404" in response.content:
                ilogger.warning(u'refresh_token_error_403',
                                u'{} {} -> {}'.format(url, params, response.text))
                self.refresh_error = 6
                self.is_active = False
                self.save()
                if v == 2:
                    raise BitrixTokenRefreshError(True, dict(error='refresh_token_error_403?'), 403,
                                                  "refresh_token_error_403")
                return False

            ilogger.exception(u'refresh_token', 'unknown error\nurl: {url}\n\ntext:\n{text}'.format(
                url=url, text=response.text
            ))

            if v == 2:
                raise BitrixTokenRefreshError(True, dict(error='response.text'), 401, "refresh_token_error")
            return False

        if response_json.get('error'):
            ilogger.warning(
                u'refresh_token_error_{}'.format(response_json.get('error')),
                u'updateurl: {} \ntoken: {} \nserver_response: {}'
                .format(url, get_admin_url(self), response.text))
            if response_json.get('error') == 'invalid_grant':
                self.refresh_error = 3
            elif response_json.get('error') == 'wrong_client':
                self.refresh_error = 1
            elif response_json.get('error') == 'expired_token':
                self.refresh_error = 2
            elif response_json.get('error') == 'NOT_INSTALLED':
                self.refresh_error = 4
            elif response_json.get('error') == 'PAYMENT_REQUIRED':
                self.refresh_error = 5
            else:
                self.refresh_error = 9
            self.is_active = False
            self.save()
            if v == 2:
                raise BitrixTokenRefreshError(True, dict(error=response_json.get('error')), 401, response_json.get('error'))
            return False
        else:
            self.refresh_error = 0

        self.auth_token = response_json.get('access_token')
        self.refresh_token = response_json.get('refresh_token')
        self.auth_token_date = timezone.now()

        try:
            # токены уволенных сотрудников успешно обновляются, но оставлять их активными нельзя
            # делаем запрос "profile", который не требует никаких разрешений
            self.call_api_method('profile', timeout=10)
        except BitrixApiError as exc:
            if (
                    # удалённый сотрудник
                    exc.is_authorization_error or exc.is_user_access_error or
                    # REST недоступен на тарифе
                    exc.is_free_plan_error
            ):
                # деактивируем токен
                self.is_active = False
                if exc.is_authorization_error:
                    self.refresh_error = self.AUTHORIZATION_ERROR
                elif exc.is_user_access_error:
                    self.refresh_error = self.USER_ACCESS_ERROR
                self.save()
                return False
        except BitrixTimeout:
            pass

        ilogger.info(u'refresh_token',
                     u'{} {} -> {}'.format(url, params, response.text))

        if self.is_active == False:
            ilogger.info(u'token_reactivated',
                         u'{} previous status={}'
                         .format(get_admin_url(self), self.get_refresh_error_display()))

        self.is_active = True
        self.save()

        return True

    def _get_throttling_redis_key(self):
        # 18.07.19 меняем подход, в случае 503 просто делаем retry через 500ms

        return 'deprecated'

        # Тут мы просто формируем название редис ключа для портала
        from .bitrix_app_installation import BitrixAppInstallation

        app_installation, _ = BitrixAppInstallation.objects.get_or_create(portal=self.user.portal,
                                                                          application=self.application)
        return 'bitrix_api_timeout_control:{}_id{}'.format(self.domain, app_installation.id)


    def call_api_method(
        self, api_method, params=None, timeout=DEFAULT_TIMEOUT,
        log_prefix='', its_logger=None, log_params=None, off_logger=False, v=None
    ):
        """см. call_api_method_v2
        """
        if v:
            ilogger.info('deprecated_call_api_method', 'call_api_method version param v deprecated')

        # using: response = token.call_api_method(api_method=method, params=fields)

        # Внимание Версия=2 v=2 должна возвращать только результат, или рейдизть ошибку
        # log_prefix создан для того чтобы отделить ошибки в логгере, в случае если нам их ловить не важно.
        # its_logger позволяет редиректить в другой логгер
        if its_logger:
            inner_logger = its_logger
        else:
            inner_logger = ilogger

        if off_logger:
            inner_logger = MuteLogger()

        if self.web_hook_auth:
            response = api_call(
                self.domain,
                api_method=api_method,
                auth_token=self.web_hook_auth,
                params=params,
                webhook=True,
                timeout=timeout,
            )

        elif hasattr(self.application, 'is_webhook') and self.application.is_webhook:
            response = api_call(
                self.domain,
                api_method=api_method,
                auth_token='{}/{}'.format(self.user.bitrix_id, self.auth_token),
                params=params,
                webhook=True,
                timeout=timeout,
            )

        else:
            try:
                response = api_call(
                    self.domain,
                    api_method=api_method,
                    auth_token=self.auth_token,
                    params=params,
                    timeout=timeout,
                )
            except ConnectionToBitrixError:
                raise BitrixApiError(False, {'error': 'ConnectionToBitrixError'}, 600, "ConnectionToBitrixError")


        # Пробуем раскодировать json
        try:
            json_response = response.json()
        except ValueError:
            # Известные исключения

            if response.content == '﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿﻿{"error":"expired_token","error_description":"The access token provided has expired."}':
                # 1 Портал отвечал в строке одинарных ковычках
                json_response = {
                    "error": "expired_token",
                    "error_description": "The access token provided has expired."
                }
            elif response.status_code == 502:
                json_response = {
                    "error": "Bad Gateway",
                    "error_description": "Bad Gateway"
                }
            elif response.reason == 'Access Denied by missing domain name':
                json_response = {
                    "error": "Access Denied by missing domain name",
                    "error_description": "Access Denied by missing domain name"
                }
            elif response.content.startswith(b'The script encountered an error and will be aborted'):
                # Бага в коробке, предлагается включить дебаг тру
                json_response = {
                    "error": "The script encountered an error and will be aborted",
                    "error_description": response.content
                }
                raise BitrixApiServerError(False, json_response, response.status_code, "server error")

            else:
                # Считаем что сервер делает что-то не то и пробелма в Битриксе
                inner_logger.warning('{}bitrix_api_server_error_{}'.format(log_prefix, response.status_code),
                                   '{}->{} code={}'.format(self.domain, api_method, response.status_code),
                                   params=log_params)
                json_response = {
                    "error": "server_error",
                    "error_description": response.text
                }
                raise BitrixApiServerError(False, json_response, response.status_code, "server error")





        # Надо доанализировать чем отвечает битиркс
        # Вектор один - коды ответа
        # Вектор 2 либо резалт либо описание ошибок
        # Вектор 3 типы ошибок
        # Возвращаем # 1)Положительный ответ? 2)Нет ошибки АПИ? 3) Данные 4) статус код
        # is_api_answered, no_error, result, code
        if response.status_code in [200, 201]:
            # Нормальные ответы
            if json_response.get('error'):
                if json_response['error'] == 'WRONG_ENCODING':
                    raise BitrixApiError(True, json_response, response.status_code, "WRONG_ENCODING")

                # Надо научиться обрабатывать все ошибки, если попало сюда, то что-то новое в АПИ
                inner_logger.error(
                    '{}api_error_2xx'.format(log_prefix),
                    #'{}->{} [{}] api error {}'.format(self.domain, api_method, get_admin_a_tag(self, 'токен'), response.text.decode('unicode_escape')),
                    '{}->{} [{}] api error {}'.format(self.domain, api_method, get_admin_a_tag(self, 'токен'), response.text),
                    params=log_params)
                raise BitrixApiError(True, json_response, response.status_code, "api_error_2xx")
            else:
                return json_response
        elif response.status_code in [500, 502, 504]:
            try:
                # возможно мы сталкивались с ответами которые человеку было сложно прочитать типа \u1444\u4144
                # но в некоторых местах ругалось AttributeError: 'str' object has no attribute 'decode'
                # поэтому трай эксепт
                inner_logger.warning('api_error_{}'.format(response.status_code),
                                     '{}->{} [{}] {}'.format(self.domain, api_method, get_admin_a_tag(self, 'токен'), response.text.decode('unicode_escape')),
                                     params=log_params)
            except Exception:
                inner_logger.warning('api_error_{}'.format(response.status_code),
                                     '{}->{} [{}] {}'.format(self.domain, api_method, get_admin_a_tag(self, 'токен'), response.text),
                                     params=log_params)

            raise BitrixApiError(False, json_response, response.status_code, "api_error")
        else:
            if response.status_code == 401 and json_response['error'] == 'expired_token':
                # Ветка обновления Токена
                success = self.refresh(timeout=timeout)
                if success:
                    # Если обновление токена прошло успешно, повторить запрос
                    return self.call_api_method(
                        api_method, params, log_prefix=log_prefix, its_logger=its_logger,log_params=log_params,
                        timeout=timeout,
                    )
                else:
                    inner_logger.warning(
                        '{}cant_refresh'.format(log_prefix),
                        '{}->{} previous error={}  [{}]'.format(self.domain, api_method, json_response['error'], get_admin_a_tag(self, 'токен')),
                        params=log_params)
                    raise BitrixApiError(True, json_response, response.status_code, "cant_refresh")

            if response.status_code == 403 and json_response['error'] == 'ACCESS_DENIED':
                # Бывает что человек был админом, но потом у него отняли права 'json_response': {'error': 'ACCESS_DENIED', 'error_description': 'Access denied!'},
                # токен гасить не нужно, но у юзера надо снять галку is_admin
                self.user.update_is_admin(self)


            cde_result = self.check_deactivate_errors(response=response,
                                                      its_logger=inner_logger,
                                                      log_prefix=log_prefix,
                                                      log_params=log_params,
                                                      api_method=api_method)
            if cde_result:
                return cde_result

            if response.status_code == 400 and json_response['error'] == 'ERROR_CORE' \
                    and json_response['error_description'] == 'Unable to set event handler: Handler already binded':
                raise BitrixApiError(True, json_response, response.status_code, "Handler already binded")


            if response.status_code == 503 and json_response['error'] == 'QUERY_LIMIT_EXCEEDED':
                raise BitrixApiError(True, {"error": "503"}, response.status_code, "503")

            if (
                    response.status_code == 403 and
                    json_response['error'] != 'PORTAL_DELETED' and
                    json_response['error_description'] != 'Access denied! Available only on extended plans' and
                    json_response['error_description'] != 'Access denied!'
            ):
                # 403 приходил без описания !!!! Но теперь умеет приходить PORTAL_DELETED
                # теперь еще умеет приходить "Access denied! Available only on extended plans"
                inner_logger.error('{}token_403_or_404'.format(log_prefix),
                                   '{}->{} [{}]'.format(self.domain, api_method, get_admin_a_tag(self, 'токен')),
                                   params=log_params)
                if response.reason == 'Access Denied by missing domain name':
                    self.is_active = False
                self.refresh_error = self.ERROR_403_or_404
                self.save(force_update=True)
                raise BitrixApiError(True, {"error": "403_or_404"}, response.status_code, "403_or_404", refresh_error=self.refresh_error)



            # Надо поймать все коды, если попало сюда, то что-то новое в АПИ
            stack_trace = traceback.format_stack(limit=20)
            stack_trace = ''.join(stack_trace)

            inner_logger.warning(
                '{}api_error_{}_{}'.format(log_prefix, response.status_code, json_response.get('error') or api_method),
                '{}->{} [{}] {}'.format(self.domain, api_method, get_admin_a_tag(self, 'токен'), json_response),
                params=log_params
            )
            raise BitrixApiError(False, json_response, response.status_code, "api_error")

    def check_deactivate_errors(self, response, its_logger=None, log_prefix='', log_params={}, api_method=''):
        # функция обрабатывает все случаи которые должны деактивировать токен
        # вынесено в отдельную функцию, для испольования в батчах
        # отключить если нужно токен
        # рейзнуть BitrixApiError
        if its_logger:
            inner_logger = its_logger
        else:
            inner_logger = ilogger

        json_response = response.json()
        deactivate_token = False
        refresh_error = None

        if response.status_code == 401 and json_response['error'] == 'APPLICATION_NOT_FOUND':
            deactivate_token = True
            refresh_error = self.APPLICATION_NOT_FOUND

        if response.status_code == 401 and json_response['error'] == 'PAYMENT_REQUIRED':
            deactivate_token = True
            refresh_error = self.PAYMENT_REQUIRED

        if response.status_code == 401 and json_response['error'] == 'ERROR_OAUTH' \
                and json_response['error_description'] == 'Application not installed':
            deactivate_token = True
            refresh_error = self.ERROR_OAUTH

        # Дезактивирует токены при переименовании портала, временно отключаю
        # if response.status_code == 401 and json_response['error'] == 'NO_AUTH_FOUND' \
        #         and json_response['error_description'] == 'Wrong authorization data':
        #     deactivate_token = True
        #     refresh_error = self.NO_AUTH_FOUND

        # if response.status_code == 401 and json_response['error'] == 'authorization_error' \
        #         and json_response['error_description'] == 'Unable to authorize user':
        #     deactivate_token = True
        #     refresh_error = self.AUTHORIZATION_ERROR

        if response.status_code == 401 and json_response['error'] == 'invalid_token' \
                and json_response['error_description'] == 'Unable to get application by token':
            deactivate_token = True
            refresh_error = self.INVALID_TOKEN

        if response.status_code == 401 and json_response['error'] == 'user_access_error' \
                and json_response['error_description'] == 'The user does not have access to the application.':
            deactivate_token = True
            refresh_error = self.USER_ACCESS_ERROR

        if response.status_code == 400 and json_response['error'] == 'ERROR_CORE' \
                and json_response['error_description'] == 'No client credentials':
            # Непонятная ошибка поэтому тестируем вместе с error_description
            deactivate_token = True
            refresh_error = self.ERROR_CORE

        if response.status_code in [403, 410] and json_response['error'] == 'PORTAL_DELETED':
            deactivate_token = True
            refresh_error = self.PORTAL_DELETED

        # комментируем т.к стал отдавать такую ошибку на crm.lead.get https://b24.it-solution.ru/workgroups/group/557/tasks/task/view/20767/
        # if response.status_code == 400 and json_response['error'] == '' \
        #         and json_response['error_description'] == 'Access denied.':
        #     # {"error":"","error_description":"Access denied."}
        #     deactivate_token = True
        #     refresh_error = self.ACCESS_DENIED

        if deactivate_token:
            inner_logger.warning('{}token_deactivated_{}'.format(log_prefix, json_response['error']),
                                 '{}->{} [{}]'.format(self.domain, api_method, get_admin_a_tag(self, 'токен')),
                                 params=log_params)
            self.is_active = False
            self.refresh_error = refresh_error
            if self.pk:
                # Для не динамических токенов которые имеют запись в БД
                self.save(force_update=True)
            raise BitrixApiError(True, json_response, response.status_code, "token_deactivated",
                                     refresh_error=refresh_error)

        return None

    def deactivate_token(self, refresh_error):
        if self.pk:
            self.is_active = False
            self.refresh_error = refresh_error
            self.save(force_update=True)

    def call_api_method_v2(
        self, api_method, params=None, timeout=DEFAULT_TIMEOUT,
        log_prefix='', its_logger=None, log_params=None, off_logger=False
    ):
        """Вызывает метод на битрикс портале с данным токеном
        и возвращает результат (словарь).

        :param api_method: например 'user.get'
        :param params: например {'ID': 42}
        :param timeout: таймаут в секундах, NB! таймаут применяется
            к каждому запросу к битриксу, так если случается
            обновление токена, то по факту он может быть утроен
            (первый запрос + refresh + повторный запрос)

        :param log_prefix: опционально префикс для ItsLogger
        :param its_logger: опционально инстанс ItsLogger
        :param log_params: дополнительный контекст для логирования
        :param off_logger: отключает логгирование полностью в вызове

        :rtype: dict
        :returns: например {'result': [<список пользователей>], 'total': 1, ...}

        :raises: BitrixApiError
        :raises: BitrixTimeout

        см. также:
            call_list_method для вызова списочных методов,
                следует использовать его, если может быть >50 записей
            batch_api_call для выполнения батч-методом до 50 запросов
                за 1 HTTP-запрос к битриксу, например можно
                обновить/удалить/создать сразу 50 записей в битриксе,
                сформировав всего 1 батч-запрос.
        """

        ilogger.info('deprecated_call_api_method_v2', 'call_api_method_v2 deprecated')

        return self.call_api_method(
            api_method,
            params=params,
            log_prefix=log_prefix,
            its_logger=its_logger,
            log_params=log_params,
            off_logger=off_logger,
            timeout=timeout,
        )

    def batch_api_call(self, methods, timeout=DEFAULT_TIMEOUT,
                          chunk_size=50, halt=0, log_prefix=''):
        """:rtype: bitrix_utils.bitrix_auth.functions.batch_api_call.BatchResultDict
        """
        try:
            # ЭТО БЫВШАЯ ФУНКЦИЯ call3!!! но переименована для integration utils
            return _batch_api_call(methods=methods,
                                    bitrix_user_token=self,
                                    function_calling_from_bitrix_user_token_think_before_use=True,
                                    timeout=timeout,
                                    chunk_size=chunk_size,
                                    halt=halt,
                                    log_prefix=log_prefix)
        except BatchApiCallError as e:
            self.check_deactivate_errors(e.reason)
            raise e

    batch_api_call_v3 = batch_api_call

    def call_list_method(self, method, fields=None, limit=None,
                         allowable_error=None, timeout=DEFAULT_TIMEOUT,
                         log_prefix='', batch_size=50):
        from integration_utils.bitrix24.functions.call_list_method import call_list_method
        return call_list_method(self, method, fields=fields,
                                limit=limit,
                                allowable_error=allowable_error,
                                timeout=timeout,
                                log_prefix=log_prefix,
                                batch_size=batch_size,
                                v=2)

    call_list_method_v2 = call_list_method

    def call_list_fast(
        self,
        method,  # type: str
        params=None,  # type: Optional[dict]
        descending=False,  # type: bool
        timeout=DEFAULT_TIMEOUT,  # type: Optional[int]
        log_prefix='',  # type: str
        limit=None,  # type: Optional[int]
        batch_size=50,  # type: int
    ):
        # type: (...) -> Iterable[Any]
        """Списочный запрос с параметром ?start=-1
        см. описание integration_utils.bitrix24.functions.call_list_fast.call_list_fast

        Если происходит KeyError, надо добавить описание метода
        в справочники METHOD_TO_* в integration_utils.bitrix24.functions.call_list_fast
        """
        from integration_utils.bitrix24.functions.call_list_fast import call_list_fast
        return call_list_fast(self, method, params, descending=descending,
                              limit=limit, batch_size=batch_size,
                              timeout=timeout, log_prefix=log_prefix)

    def call_snapi_method(self, method, params=None):
        """
        https://ts.it-solution.ru/#/ticket/58954/

        Вызов snapi
        """

        json_params = dict(auth=self.auth_token, bitrix_domain=self.domain)
        if params:
            json_params.update(params)

        response = requests.post('{}{}/'.format(self.SNAPI_URL, method), json=json_params)

        try:
            json_response = response.json()

        except ValueError:
            raise SnapiError(False, response.text, response.status_code, "response parsing error")

        error = json_response.get('error')
        if error:
            if error.get('error_code') == 'BITRIX_EXPIRED_TOKEN_ERROR' and self.refresh():
                return self.call_snapi_method(method, params)

            raise SnapiError(True, json_response, response.status_code, "snapi error")

        return json_response

    @classmethod
    def refresh_all(cls, timeout=DEFAULT_TIMEOUT):
        """Обновить все токены, неудачи игнорятся.

        :param timeout: таймаут обновления каждого конкретного токена.
        """
        # to_refresh = BitrixUserToken.objects.filter(is_active=True)
        to_refresh = BitrixUserToken.objects.filter(application__is_webhook=False)
        active_from = to_refresh.filter(is_active=True).count()
        active_to = 0
        for instance in to_refresh:
            if instance.refresh(timeout=timeout):
                active_to += 1
        return "%s -> %s" % (active_from, active_to)

    def hello_world(self, *args, **kwargs):  # ?
        return u'hello_world'

    def __unicode__(self):
        try:
            return u"#{}@{} of {!r}".format(self.id, self.domain, self.user if self.id else 'dynamic_token')
        except:
            return u"#{}@{} of user.{!r}".format(self.id, self.domain, self.user_id if self.id else 'dynamic_token')

    __str__ = __unicode__


BitrixUserTokenDoesNotExist = BitrixUserToken.DoesNotExist
