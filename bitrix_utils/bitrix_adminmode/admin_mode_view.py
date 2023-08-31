from typing import TYPE_CHECKING, Callable, Dict

from django.http import HttpRequest
from django.http.response import HttpResponseBase
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from its_utils.app_get_params import get_params_from_sources
from bitrix_utils.bitrix_auth.functions.bitrix_auth_required import bitrix_auth_required

if TYPE_CHECKING:
    from bitrix_utils.bitrix_adminmode.admin_mode_settings import AdminModeSettings
    from bitrix_utils.bitrix_adminmode.admin_mode_view_param import AdminModeViewParam


class AdminModeView:
    VIEW_NAME = NotImplemented
    TITLE = NotImplemented
    TEMPLATE_NAME = NotImplemented

    ADMIN_USER_REQUIRED = True
    PARAMS = {}  # type: Dict[str, AdminModeViewParam]

    def __init__(self, request: HttpRequest, admin_mode_settings: 'AdminModeSettings'):
        self.request = request
        self.admin_mode_settings = admin_mode_settings

    @classmethod
    def url_path(cls):
        return '{}/'.format(cls.VIEW_NAME)

    @classmethod
    def as_view(cls, admin_mode_settings: 'AdminModeSettings') -> Callable:
        @csrf_exempt
        @bitrix_auth_required(*admin_mode_settings.application_codes)
        def view(request, **kwargs):
            admin_mode_view = cls(request, admin_mode_settings)
            params = {param: kwargs[param] for param in cls.PARAMS.keys()}
            return admin_mode_view.get_response(request=request, params=params)

        for param_name, param_object in cls.PARAMS.items():
            view = param_object.decorate(view=view, param_name=param_name)
        view = get_params_from_sources(view)  # так get_params_from_sources отработает раньше expect_param

        return view

    @property
    def full_view_name(self):
        return self.admin_mode_settings.get_full_view_name(self)

    def get_response(self, request: HttpRequest, params: dict):
        if self.ADMIN_USER_REQUIRED and not request.bx_user.is_admin:
            return render(request, 'bitrix_adminmode/admin_user_required.html')

        if request.method == 'POST':
            return self.process_post(request=request, params=params)

        context = self.get_context(request=request, params=params)
        context.update(dict(
            admin_mode_settings=self.admin_mode_settings,
            admin_mode_view=self,
            admin_mode_view_params=params,
        ))

        return render(
            request=request,
            template_name=self.TEMPLATE_NAME,
            context=context,
        )

    def get_context(self, request: HttpRequest, params: dict) -> dict:
        """
        Получить контекст для функции render
        """

        return dict()

    def process_post(self, request: HttpRequest, params: dict) -> HttpResponseBase:
        return redirect(self.full_view_name)
