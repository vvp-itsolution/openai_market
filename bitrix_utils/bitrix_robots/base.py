from functools import wraps
from typing import Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse, QueryDict, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from its_utils.app_get_params import get_params_from_sources
from bitrix_utils.bitrix_auth.models import BitrixUser, BitrixUserToken, BitrixPortal, BitrixApp
from ..bitrix_auth.functions.bitrix_auth_required import bitrix_auth_required

try:
    from its_logger import its_logger
except ImportError:  # compat
    from settings import ilogger as its_logger
from .errors import VerificationError
from .helpers import get_php_style_list


class RobotBase(object):
    """Робот для базы знаний,
    бойлерплейт не связанный с бизнес-логикой.

    https://dev.1c-bitrix.ru/rest_help/bizproc/bizproc_robot/bizproc_robot_add.php

    Роботу нужнен список допустимых названий приложения,
    для проверки подлинности запросов, можно определить в настройках:

    BITRIX_APP_CODE - если код 1
    BITRIX_APP_CODES - если несколько

    Либо можно определить BITRIX_APP_CODES при наследовании:

        class SomeRobot(RobotBase):
            BITRIX_APP_CODES = ['itsolutionru.someapp']
            ...

    Пример робота: см. HelloWorldRobot
    """
    try:
        BITRIX_APP_CODES = settings.BITRIX_APP_CODES
    except AttributeError:
        try:
            BITRIX_APP_CODES = [settings.BITRIX_APP_CODE]
        except AttributeError:
            BITRIX_APP_CODES = NotImplemented

    CODE = NotImplemented
    NAME = NotImplemented
    # {'error': 'ERROR_ACTIVITY_VALIDATION_FAILURE',
    #  'error_description': 'USE_SUBSCRIPTION is not supported in Robots!'}
    # USE_SUBSCRIPTION = True  # Что это?
    PROPERTIES = {}
    USE_PLACEMENT = False  # Проверить если потребуется, пока заготовка

    # USE_SUBSCRIPTION = None: пользователь выбирает ждать ли ответа (работает ненадежно)
    # USE_SUBSCRIPTION = True: всегда ждать ответа робота
    # USE_SUBSCRIPTION = False: никогда не ждать ответа робота
    USE_SUBSCRIPTION = None

    RETURN_PROPERTIES = {}

    # Обрабатывать запрос сразу после получения. Если False, необходимо определить метод delay_process
    PROCESS_ON_REQUEST = True

    # Создавать пользователя, если процесс запущен от имени отсутствующего в базе
    CREATE_USERS = True

    def __init__(self,
                 params: dict,
                 portal: Optional[BitrixPortal] = None,
                 app_code: Optional[str] = None,
                 event_token: Optional[str] = None,
                 request: Optional[HttpRequest] = None):
        # параметр request остаётся для обратной совместимости. process() может вызываться отложенно без request'а
        self.request = request
        # request.its_params
        self.params = params
        # портал и код прило устанавливается после проверки события
        self.portal = portal
        self.app_code = app_code
        # Токен ответа действия для bizproc.event.send
        self.event_token = event_token

    @classmethod
    def from_request(cls, request: HttpRequest):
        return cls(
            params=request.its_params,
            request=request,
        )

    @classmethod
    def as_view(cls):
        @get_params_from_sources
        @csrf_exempt
        @wraps(cls.start_process)
        def view(request):
            cls_name = type(cls).__name__

            its_logger.debug(
                'new_robot_request',
                '{cls}\nPOST: {request.POST!r}'.format(cls=cls_name, request=request),
            )

            robot = cls.from_request(request)

            try:
                robot.verify_event()
            except VerificationError as e:
                its_logger.error(
                    'robot_verification_error',
                    '{cls}: {e!r}\nPOST: {request.POST!r}'.format(
                        cls=cls_name, e=e, request=request,
                    ),
                )
                return e.http_response()

            try:
                response = robot.start_process()
            except Exception as e:
                its_logger.error(
                    'robot_processings_error',
                    '{cls} at {p}: {e!r}\nPOST: {request.POST!r}'.format(
                        cls=cls_name, p=robot.portal, e=e, request=request,
                    ),
                )
                return HttpResponse('error')

            # есть ли смысл возвращать битриксу какой-то другой ответ?
            return response

        return view

    @classmethod
    def as_hook(cls):
        @csrf_exempt
        @get_params_from_sources
        @bitrix_auth_required(*cls.BITRIX_APP_CODES)
        @wraps(cls.process)
        def view(request):
            result = cls(
                params=request.its_params,
                portal=request.bx_portal,
                app_code=request.bx_user_token.application.name,
            ).process(
                token=request.bx_user_token,
                props=request.its_params.get('properties'),
            )

            if isinstance(result, HttpResponse):
                return result

            return JsonResponse(result)

        return view

    @classmethod
    def handler_url(cls, view_name):
        """Получить URL обработчика через reverse+название view
        """
        return 'https://{domain}{path}'.format(
            domain=settings.DOMAIN,
            path=reverse(view_name),
        )

    @classmethod
    def _robot_add_params(cls, view_name: str, bx_user_bitrix_id: int) -> dict:
        def bx_bool(value):
            return 'Y' if value else 'N'

        params = dict(
            AUTH_USER_ID=bx_user_bitrix_id,
            CODE=cls.CODE,
            HANDLER=cls.handler_url(view_name),
            NAME=cls.NAME,
            USE_PLACEMENT=bx_bool(cls.USE_PLACEMENT),
        )

        # Если передавать пустые объекты возникает ошибка:
        # {'error_description': 'Wrong property key (0)!',
        #  'error': 'ERROR_ACTIVITY_VALIDATION_FAILURE'}
        if cls.PROPERTIES:
            params['PROPERTIES'] = cls.PROPERTIES
        if cls.RETURN_PROPERTIES:
            params['RETURN_PROPERTIES'] = cls.RETURN_PROPERTIES
        if cls.USE_SUBSCRIPTION is not None:
            params['USE_SUBSCRIPTION'] = bx_bool(cls.USE_SUBSCRIPTION)

        return params

    @classmethod
    def _robot_update_params(cls, view_name: str, bx_user_bitrix_id: int) -> dict:
        add_params = cls._robot_add_params(view_name, bx_user_bitrix_id)
        code = add_params.pop('CODE')

        return dict(CODE=code, FIELDS=add_params)

    @classmethod
    def is_installed(cls, admin_token: BitrixUserToken) -> bool:
        """Зарегистрирован ли робот на портале
        """

        robot_codes = admin_token.call_list_method_v2('bizproc.robot.list')

        return any(code == cls.CODE for code in robot_codes)

    @classmethod
    def install(cls, view_name: str, admin_token: BitrixUserToken,
                token_user: Optional[BitrixUser] = None):
        """Встроить робота на портал
        """
        if token_user:
            assert token_user.id == admin_token.user_id
        else:
            token_user = admin_token.user

        return admin_token.call_api_method(
            'bizproc.robot.add',
            params=cls._robot_add_params(view_name, token_user.bitrix_id),
        )['result']

    @classmethod
    def delete(cls, admin_token: BitrixUserToken):
        """Удалить робота с портала
        """

        return admin_token.call_api_method(
            'bizproc.robot.delete',
            params=dict(CODE=cls.CODE),
        )['result']

    @classmethod
    def update(cls, view_name: str, admin_token: BitrixUserToken,
               token_user: Optional[BitrixUser] = None):
        """Обновить параметры робота на портале
        """
        if token_user:
            assert token_user.id == admin_token.user_id
        else:
            token_user = admin_token.user

        return admin_token.call_api_method(
            'bizproc.robot.update',
            params=cls._robot_update_params(view_name, token_user.bitrix_id),
        )['result']

    @classmethod
    def install_or_update(cls, view_name: str, admin_token: BitrixUserToken,
                          token_user: BitrixUser = None):
        """Встроить или обновить параметры робота на портале
        """
        if cls.is_installed(admin_token):
            method = cls.update
        else:
            method = cls.install

        method(view_name=view_name, admin_token=admin_token, token_user=token_user)

    def verify_event(self) -> None:
        """Проверка подлинности присланного события.
        Несколько усложняется тем, что у нас несколько приложений Базы Знаний.

        :raises: VerificationError
        """
        # 1. Получаем параметры авторизации
        auth = {}
        for key in ['member_id', 'access_token', 'application_token']:
            auth_key = 'auth[{}]'.format(key)
            try:
                auth[key] = self.params[auth_key]
            except KeyError:
                raise VerificationError('no {}'.format(key))
        try:
            self.event_token = self.params['event_token']
        except KeyError:
            raise VerificationError('no event token (POST[event_token])')

        # 2. Берем портал по member_id
        try:
            self.portal = BitrixPortal.objects.get(active=True, member_id=auth['member_id'])
        except BitrixPortal.DoesNotExist:
            raise VerificationError(
                'portal not found: member_id %s' % auth['member_id'])

        # 3. Проверяем верифицируется ли запрос для любого из наших приложений
        for app_code in self.BITRIX_APP_CODES:
            if self.portal.verify_online_event(
                    application_name=app_code,
                    access_token=auth['access_token'],
                    application_token=auth['application_token'],
            ):
                # 4. Запоминаем к какому приложению относится запрос
                self.app_code = app_code
                return

        # Иначе апрос с нашей точки зрения поддельный, авторизация недостоверна
        raise VerificationError('invalid auth: %r' % auth)

    def get_dynamic_token(self) -> BitrixUserToken:
        """Конструирует динамический BitrixUserToken.
        """
        return BitrixUserToken(
            auth_token=self.params["auth[access_token]"],
            domain=self.portal.domain,
        )

    def get_bx_app(self):
        return BitrixApp.objects.get(name=self.app_code)

    def get_bx_user(self) -> Optional[BitrixUser]:
        """Возвращает пользователя, кому принадлежит токен.
        """
        try:
            user = BitrixUser.objects.get(
                portal=self.portal,
                bitrix_id=self.params["auth[user_id]"],
            )

        except BitrixUser.DoesNotExist:
            if not self.CREATE_USERS:
                return None

            user = BitrixUser.objects.create(
                portal=self.portal,
                bitrix_id=self.params["auth[user_id]"],
            )
            BitrixUserToken.objects.get_or_create(
                application=self.get_bx_app(),
                user=user,
                defaults=dict(
                    auth_token=self.params['auth[access_token]'],
                    refresh_token=self.params.get('auth[refresh_token]', ''),
                    auth_token_date=timezone.now(),
                    is_active=True,
                ),
            )

        return user

    def collect_props(self) -> dict:
        """Разбирает присланные данные на основании PROPERTIES
        """

        res = {}
        query_dict_params = self.query_dict_params()
        for prop, desc in self.PROPERTIES.items():
            full_prop = 'properties[%s]' % prop
            # иногда параметры приходят в виде 'properties[prop_name][0]', даже если поле не множественное
            full_prop_0 = 'properties[%s][0]' % prop
            default = desc.get('Default')

            if desc.get('Multiple') == 'Y':
                res[prop] = get_php_style_list(query_dict_params, full_prop, [])
            else:
                res[prop] = self.params.get(full_prop, self.params.get(full_prop_0, default))

        return res

    def use_subscription(self):
        return self.params.get('use_subscription') == 'Y'

    def auth_user_id(self):
        return self.params["auth[user_id]"]

    def query_dict_params(self):
        query_dict = QueryDict('', mutable=True)
        query_dict.update(self.params)
        return query_dict

    @staticmethod
    def fix_return_values(return_values):
        fixed_return_values = {}

        for key, value in return_values.items():
            if isinstance(value, bool):
                value = 'Y' if value else 'N'
            fixed_return_values[key] = value

        return fixed_return_values

    def send_result(self, token: BitrixUserToken, return_values: dict):
        if not self.use_subscription():
            # бп не ждёт результат
            return

        try:
            token.call_api_method('bizproc.event.send', dict(
                event_token=self.event_token,
                return_values=self.fix_return_values(return_values),
            ))

        except Exception as exc:
            if getattr(exc, 'error', None) == 404:
                # процесс удалён
                return

            if self.use_subscription():
                its_logger.warning('robot_send_result_error', '{} at {}: {}'.format(
                    type(self).__name__, self.portal, exc
                ))

    def start_process(self) -> HttpResponse:
        """
        Метод вызывается из as_view()
        По умолчанию сразу вызывает process(). Можно переопределить, чтобы положить запрос в очередь
        :return:
        """

        self.token = self.get_dynamic_token()
        self.props = self.collect_props()
        self.user = self.get_bx_user()

        if self.PROCESS_ON_REQUEST:
            result = self.process(self.token, self.props)
            if isinstance(result, HttpResponse):
                return result
            if isinstance(result, dict) and self.use_subscription():
                self.send_result(self.token, return_values=result)
                return JsonResponse(result)
            return HttpResponse()

        return self.delay_process()

    def process(self, token: BitrixUserToken, props: dict) -> Optional[dict]:
        """Обработать поступивший запрос и выполнить действие робота.
        token - динамический токен
        props - входные параметры робота
        self.params - все параметры, пришедшие с запросом
        :return: если PROCESS_ON_REQUEST == True, можно вернуть словарь - return_values для send_result
        """
        raise NotImplementedError

    def delay_process(self) -> HttpResponse:
        """
        Отложить обработку запроса (положить запрос в очередь)
        """

        if not self.PROCESS_ON_REQUEST:
            raise NotImplementedError
