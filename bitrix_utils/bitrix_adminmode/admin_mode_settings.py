from typing import TYPE_CHECKING, Sequence, Type, List, Optional, Union, Dict

from django.shortcuts import redirect
from django.urls import path

from bitrix_utils.bitrix_adminmode.views import PortalLogView
from bitrix_utils.bitrix_auth.models import BitrixPortal
from bitrix_utils.bitrix_adminmode.models import PortalLog
from bitrix_utils.bitrix_adminmode.portal_logger import PortalLogger

if TYPE_CHECKING:
    from bitrix_utils.bitrix_adminmode.admin_mode_view import AdminModeView


class AdminModeSettings:
    def __init__(self,
                 app_name: str,
                 application_codes: Sequence[str],
                 title: str,
                 portal_logger_class: Optional[Type['PortalLogger']] = PortalLogger,
                 log_record_model: Type[PortalLog] = PortalLog,
                 portal_log_view_class: Optional[Type['PortalLogView']] = PortalLogView,
                 extra_view_classes: Sequence[Type['AdminModeView']] = tuple()):
        """
        :param app_name: имя приложения (совпадает с app_name в urls.py)
        :param application_codes: коды приложения для bitrix_auth_required
        :param title: заголовок
        :param portal_logger_class: класс логгера
        :param log_record_model: модель записей лога
        :param portal_log_view_class: класс вкладки 'Лог'
        :param extra_view_classes: список дополнительных вкладок (классов-потомков AdminModeView)
        """

        self.app_name = app_name
        self.application_codes = application_codes
        self.title = title
        self.portal_logger_class = portal_logger_class
        self.log_record_model = log_record_model
        self.portal_log_view_class = portal_log_view_class
        self.extra_view_classes = extra_view_classes

    @property
    def logged_app_name(self) -> str:
        return self.app_name

    def get_view_classes(self) -> List[Type['AdminModeView']]:
        view_classes = []
        if self.portal_log_view_class:
            view_classes.append(self.portal_log_view_class)
        view_classes.extend(list(self.extra_view_classes))
        return view_classes

    def get_full_view_name(self, view: Union[Type['AdminModeView'], 'AdminModeView']):
        return '{}:{}'.format(self.app_name, view.VIEW_NAME)

    def get_view_dicts(self) -> List[dict]:
        return [
            dict(title=view.TITLE, view_name=self.get_full_view_name(view))
            for view
            in self.get_view_classes()
        ]

    def index_view(self):
        def view(request):
            return redirect(self.get_full_view_name(self.get_view_classes()[0]))

        return view

    def get_index_view_name(self):
        return '{}_admin_mode'.format(self.app_name)

    def urls(self):
        url_patterns = [
            path('', self.index_view(), name=self.get_index_view_name())
        ]

        url_patterns.extend(
            path(view.url_path(), view.as_view(admin_mode_settings=self), name=view.VIEW_NAME)
            for view
            in self.get_view_classes()
        )

        return url_patterns

    def get_portal_logger(self, portal: BitrixPortal, **kwargs) -> PortalLogger:
        return self.portal_logger_class(
            app=self.logged_app_name,
            portal=portal,
            record_model=self.log_record_model,
            **kwargs,
        )
