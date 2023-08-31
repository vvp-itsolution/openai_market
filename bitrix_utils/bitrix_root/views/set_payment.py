# -*- coding: UTF-8 -*-
import datetime

import dateutil
import json
from django.conf import settings
from django.http.response import HttpResponse, HttpResponseForbidden, JsonResponse, HttpResponseNotFound
from django.utils.module_loading import import_string
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

from its_utils.app_admin.get_admin_url import get_admin_a_tag
from its_utils.app_get_params import get_params_from_sources
from its_utils.app_get_params.decorators import expect_param
from its_utils.app_get_params.functions import isodate_param
from settings import ilogger

apply_root_data_function_name = 'apply_root_data'

@csrf_exempt
@get_params_from_sources
@expect_param('portal', coerce=str)
@expect_param('portal_settings_class', coerce=str)
@expect_param('date_time_field', coerce=str)
@expect_param('portal_field', coerce=str)
@expect_param('expired', coerce=isodate_param)
@expect_param('params', coerce=str)
@expect_param('secret', coerce=str)
def set_payment(request, portal, portal_settings_class, date_time_field, portal_field, expired, params, secret):
    # Добавить в урлс
    # from bitrix_utils.bitrix_auth.views.set_payment import set_payment
    # path('its/set_payment/', set_payment),

    if secret != getattr(settings, 'SET_PAYMENT_SECRET', 'paper_keymepe'):
        return HttpResponseForbidden()

    import_class = import_string(portal_settings_class)
    try:
        portal_setting = import_class.objects.get(**{"{}__domain".format(portal_field):portal})
    except import_class.DoesNotExist:
        return HttpResponseNotFound()
    expire_date_current = getattr(portal_setting, date_time_field)
    expired_before = expire_date_current
    expire_date_new = expired

    setattr(portal_setting, date_time_field, expire_date_new)
    portal_setting.save(update_fields=[date_time_field])
    expired_after = expire_date_new
    ilogger.info('changed_pay_date', '{} {}->{}'.format(get_admin_a_tag(portal_setting), expire_date_current, expire_date_new), log_to_cron=True)
    # elif expire_date_new < expire_date_current:
    #     ilogger.info('changed_to_early_date', '{} {}->{}'.format(
    #         get_admin_a_tag(portal_setting), expire_date_current, expire_date_new), log_to_cron=True)

    apply_root_data_function = getattr(portal_setting, apply_root_data_function_name, None)
    if callable(apply_root_data_function):
        apply_root_data_function(
            portal_data=json.loads(params),
            expire_date_increased=expired_after,
            expire_date_initial=expired_before
        )
    return JsonResponse(dict(
        status='ok',
        expired_after=expired_after,
        expired_before=expired_before))
