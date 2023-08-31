from typing import Callable

from django.db import models
from django.utils import timezone
from django.conf import settings

from integration_utils.bitrix_robots.errors import VerificationError
from integration_utils.bitrix_robots.base import BaseBitrixRobot
from bitrix_utils.bitrix_auth.functions.bitrix_auth_required import bitrix_auth_required
from bitrix_utils.bitrix_auth.models import BitrixUserToken, BitrixUser, BitrixPortal, BitrixApp


class BaseRobot(BaseBitrixRobot):
    try:
        BITRIX_APP_CODES = settings.BITRIX_APP_CODES
    except AttributeError:
        try:
            BITRIX_APP_CODES = [settings.BITRIX_APP_CODE]
        except AttributeError:
            BITRIX_APP_CODES = NotImplemented

    APP_DOMAIN = settings.DOMAIN  # type: str

    portal = models.ForeignKey('bitrix_auth.BitrixPortal', on_delete=models.PROTECT)
    token = models.ForeignKey('bitrix_auth.BitrixUserToken', on_delete=models.PROTECT)

    class Meta:
        abstract = True

    class Admin(BaseBitrixRobot.Admin):
        list_display = 'id', 'portal', 'token', 'dt_add', 'started', 'finished', 'is_success'
        list_display_links = list_display
        search_fields = ['portal__domain']
        raw_id_fields = 'portal', 'token',

    @classmethod
    def get_hook_auth_decorator(cls) -> Callable:
        return bitrix_auth_required(*cls.BITRIX_APP_CODES)

    @classmethod
    def from_hook_request(cls, request) -> 'BaseBitrixRobot':
        return cls.objects.create(
            portal=request.bx_portal,
            token=request.bx_user_token,
            params=request.its_params,
            is_hook_request=True,
        )

    def verify_event(self):
        """Проверка подлинности присланного события.
        Несколько усложняется тем, что у нас несколько приложений Базы Знаний.

        :raises: VerificationError
        """
        # 1. Получаем параметры авторизации
        auth = self.get_auth_dict()

        try:
            self.event_token = self.params['event_token']
        except KeyError:
            raise VerificationError('no event token (POST[event_token])')

        # 2. Берем портал по member_id
        try:
            self.portal = BitrixPortal.objects.get(active=True, member_id=auth['member_id'])
        except BitrixPortal.DoesNotExist:
            raise VerificationError('portal not found: member_id %s' % auth['member_id'])

        # 3. Проверяем верифицируется ли запрос для любого из наших приложений
        for app_code in self.BITRIX_APP_CODES:
            if self.portal.verify_online_event(
                    application_name=app_code,
                    access_token=auth['access_token'],
                    application_token=auth['application_token'],
            ):
                # 4. Сохраняем токен
                user, _ = BitrixUser.objects.get_or_create(portal=self.portal, bitrix_id=auth['user_id'])
                app = BitrixApp.objects.get(name=app_code)
                self.token, _ = BitrixUserToken.objects.get_or_create(
                    user=user,
                    application=app,
                    defaults=dict(
                        auth_token=auth['access_token'],
                        refresh_token=self.params.get('auth[refresh_token]', ''),
                        auth_token_date=timezone.now(),
                        is_active=True,
                    ),
                )
                return

        # Иначе апрос с нашей точки зрения поддельный, авторизация недостоверна
        raise VerificationError('invalid auth: %r' % auth)

    def process(self) -> dict:
        """
        Обработать запрос
        self.props - параметры
        self.portal - портал
        self.token - токен
        """
        raise NotImplementedError
