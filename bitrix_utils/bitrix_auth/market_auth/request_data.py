from django.utils import timezone

from bitrix_utils.bitrix_auth.exceptions import BitrixApiError
from bitrix_utils.bitrix_auth.functions.dec_bitrix_start_point import get_portal_domain_and_member_id, EnterFromBitrix
from bitrix_utils.bitrix_auth.models import BitrixUserToken, BitrixApp, BitrixPortal, BitrixUser
from integration_utils.bitrix24.functions.api_call import BitrixTimeout, ConnectionToBitrixError
from integration_utils.bitrix24.functions.batch_api_call import BatchApiCallError
from settings import ilogger


class RequestData:
    # Попробуем сделать крутой новый класс для параметров?
    START_POINT_REQUESTS_TIMEOUT = 15

    def __init__(self):
        self.auth_token = ''
        self.refresh_token = ''
        self.app_sid = ''
        self.member_id = ''
        self.domain = ''

        self.user_info = ''
        self.admin_info = ''
        self.app_info = ''

        # Модели
        self.bitrix_app = None
        self._bitrix_portal = None
        self._bitrix_user: BitrixUser = None
        self.bitrix_user_token: BitrixUserToken = None

    @property
    def user_token_sig(self):
        return '{}::{}'.format(self.bitrix_user_token.id, BitrixUserToken.get_auth_token(self.bitrix_user_token.id))

    @property
    def bitrix_portal(self):
        if not  self._bitrix_portal:
            self._bitrix_portal = self.bitrix_user_token.user.portal
        return self._bitrix_portal

    @property
    def bitrix_user(self):
        if not self._bitrix_user:
            self._bitrix_user = self.bitrix_user_token.user
        return self._bitrix_user

    def from_iframe_data(self, request):
        # Вытаскиваются стандартные параметры из iframe данных, когда приложение запускается в айфрейм или встройки
        self.auth_token = request.POST.get('AUTH_ID')
        self.refresh_token = request.POST.get('REFRESH_ID')
        self.app_sid = request.GET.get('APP_SID')

    def from_user_token_sig(self, request):
        # Авторизация заголовком
        http_user_token_sig = request.META.get('HTTP_AUTHORIZATION')
        self.bitrix_user_token = BitrixUserToken.get_by_token(http_user_token_sig)
        return True

    def fill_portal_data(self):
        # Полсе этого должен заполниться member_id и domain
        self.domain, self.member_id = get_portal_domain_and_member_id(self.auth_token)



    def fill_from_batch(self):
        # Запрашиваем всю информацию о пользователе и портале
        # Иногда, приложению будет не хватать прав на запрос, например, групп
        # Тогда надо просто игнорировать эту информацию и попытаться записать все что можно
        # Минимум, который нужен - это информация о пользователе
        methods = [
            ('user_info', 'user.current', None),
            ('admin_info', 'user.admin', None),
            #('user_groups', 'sonet_group.user.groups', None),
            ('app_info', 'app.info', None),
        ]

        try:
            dynamic_token = BitrixUserToken(auth_token=self.auth_token, domain=self.domain)
            batch_response = dynamic_token.batch_api_call(methods, timeout=self.START_POINT_REQUESTS_TIMEOUT)
        except BitrixTimeout:
            raise EnterFromBitrix('Сервер Битрикс24 %s недоступен' % self.domain)
        except BitrixApiError as e:
            ilogger.error(u'failed_attempt_to_enter', 'err')
            raise EnterFromBitrix('Не удалось получить информацию о пользователе')
        except BatchApiCallError as e:
            ilogger.error(u'failed_attempt_to_enter_{}'.format(e.reason), 'err')
            raise EnterFromBitrix('Не удалось получить информацию о пользователе')
        except ConnectionToBitrixError as e:
            ilogger.error(u'failed_attempt_to_enter_connection_error', 'err')
            raise EnterFromBitrix('Портал не отвечает по https. Проверьте ssl сертификат или файерволл')

        self.user_info = batch_response['user_info']['result']
        self.admin_info = batch_response['admin_info']['result']
        self.app_info = batch_response['app_info']['result']

    def check_app_data(self):
        # Токены могут быть и правильные, но этот сервер может не обслуживать это приложение
        app_code = self.app_info.get('CODE')
        try:
            bitrix_app = BitrixApp.objects.get(name=app_code)
        except BitrixApp.DoesNotExist:
            ilogger.error(u'bitrix_app_code_not_found=> {}'.format(app_code))
            raise
        self.bitrix_app = bitrix_app

    def fill_portal(self):
        # member_id - уникальный id портала
        # https://dev.1c-bitrix.ru/learning/course/?COURSE_ID=43&LESSON_ID=4997
        portal, portal_created = BitrixPortal.objects.get_or_create(member_id=self.member_id)
        portal.domain = self.domain
        portal.active = True
        portal.save()
        self._bitrix_portal = portal

    def fill_user(self):
        # Создаем или обновляем юзера
        user, user_created = BitrixUser.objects.get_or_create(portal=self.bitrix_portal, bitrix_id=int(self.user_info['ID']))
        user.update_from_bx_response(user=self.user_info, save=False)
        user.is_admin = self.admin_info  # админ ли юзер?
        user.user_is_active = True  # если дошел до сюда - точно активный
        user.save()
        self._bitrix_user = user

    def fill_token(self):
        # Создаем или обновляем токен
        if not self.bitrix_app:
            # Не надо без приложения токенов
            raise

        bitrix_user_token, _ = BitrixUserToken.objects.get_or_create(
            application=self.bitrix_app, user=self.bitrix_user, defaults={'auth_token_date': timezone.now()})

        # Заполнение полей токена
        bitrix_user_token.auth_token = self.auth_token

        if self.refresh_token:
            bitrix_user_token.refresh_token = self.refresh_token
        elif not self.bitrix_user.id:
            # т. к. для refresh_token is_null=False, присвоим пустую строку новому токену
            bitrix_user_token.refresh_token = ''

        bitrix_user_token.auth_token_date = timezone.now()
        bitrix_user_token.is_active = True
        bitrix_user_token.refresh_error = 0
        bitrix_user_token.application = self.bitrix_app
        if self.app_sid is not None:
            bitrix_user_token.app_sid = self.app_sid
        bitrix_user_token.save()
        self.bitrix_user_token = bitrix_user_token