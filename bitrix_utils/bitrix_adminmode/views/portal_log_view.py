from typing import Any, Dict, Union, Sequence

from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.urls import reverse

from bitrix_utils.bitrix_auth.models import BitrixPortal
from its_utils.app_get_params.functions import int_param

from bitrix_utils.bitrix_adminmode.admin_mode_view import AdminModeView
from bitrix_utils.bitrix_adminmode.admin_mode_view_param import AdminModeViewParam
from bitrix_utils.bitrix_adminmode.models import PortalLog


class PortalLogView(AdminModeView):
    VIEW_NAME = 'log'
    TITLE = 'Лог'
    TEMPLATE_NAME = 'bitrix_adminmode/portal_log.html'

    PARAMS = dict(
        page=AdminModeViewParam(coerce=int_param, default=1),
    )

    RECORDS_PER_PAGE = 100

    def get_portal_log_qs(self, portal: BitrixPortal, params: dict) -> 'QuerySet[PortalLog]':
        """
        Получить все записи лога на портале
        """

        return self.admin_mode_settings.log_record_model.objects.filter(
            app__name=self.admin_mode_settings.logged_app_name,
            portal=portal,
        )

    def get_page_records(self, qs: 'QuerySet[PortalLog]', page: int) -> 'QuerySet[PortalLog]':
        """
        Получить записи для одонй страницы
        """

        log_records = qs.order_by('-id')

        if self.RECORDS_PER_PAGE is not None:
            offset = self.RECORDS_PER_PAGE * (page - 1)
            log_records = log_records[offset:offset + self.RECORDS_PER_PAGE + 1]

        return log_records

    def get_log_records(self, request: HttpRequest, params: dict) -> Union['QuerySet[PortalLog]', Sequence[Any]]:
        """
        Получить отфильтрованный и упорядоченный набор или список записей лога
        """

        # получить все записи
        log_records = self.get_portal_log_qs(portal=request.bx_portal, params=params)

        # отобрать для текущей страницы
        log_records = self.get_page_records(qs=log_records, page=params['page'])

        return log_records

    def get_page_url(self, request: HttpRequest, page: int) -> str:
        """
        Получить url страницы
        """

        get_params = ['{}={}'.format(param, request.GET[param]) for param in request.GET.keys() if param != 'page']
        get_params.append('page={}'.format(page))
        return '{}?{}'.format(
            reverse(self.full_view_name),
            '&'.join(get_params)
        )

    def get_context(self, request: HttpRequest, params: dict) -> Dict[str, Any]:
        return dict(
            log_records=self.get_log_records(request=request, params=params),
            records_per_page=self.RECORDS_PER_PAGE,
            page=params['page'],
            next_page_url=self.get_page_url(request, params['page'] + 1),
            prev_page_url=self.get_page_url(request, params['page'] - 1),
        )
