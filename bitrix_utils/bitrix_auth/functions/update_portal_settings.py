# -*- coding: utf-8 -*-

import requests
from datetime import datetime
from django.utils.module_loading import import_string

from its_utils.app_admin.get_admin_url import get_admin_a_tag
from settings import ilogger

URL = 'https://rootapp.it-solution.ru/bundle/get_payment_info'
apply_root_data_function_name = 'apply_root_data'

"""
Документация
https://it-solution.kdb24.ru/article/80784/

"""

# def update_portal_settings(settings_class, date_time_field, app_code, boolean_field=''):
def update_portal_settings(settings_class, date_time_field, app_code, portal_field='portal'):
    ilogger.warning('update_portal_settings_deprecated', 'yes')
    import_class = import_string(settings_class)

    portal_settings_query = import_class.objects.all()

    for portal_settings in portal_settings_query:
        response = requests.get(URL, params={'portal': getattr(portal_settings, portal_field).domain, 'app_code': app_code})
        if response.ok and response.status_code == 200:
            response_data = response.json()

            expire_date_current = getattr(portal_settings, date_time_field)
            expire_date_increased = False

            if 'date' in response_data and response_data['date']:
                expire_date_response = datetime.strptime(response_data['date'], '%Y-%m-%d').date()

                if not expire_date_current or expire_date_response > expire_date_current:
                    setattr(portal_settings, date_time_field, expire_date_response)
                    # if boolean_field:
                    #     setattr(portal_settings, boolean_field, True)
                    portal_settings.save(update_fields=[date_time_field])
                    expire_date_increased = True
                    ilogger.info('changed_pay_date', '{} {}->{}'.format(
                        get_admin_a_tag(portal_settings), expire_date_current, expire_date_response), log_to_cron=True)
                elif expire_date_response < expire_date_current:
                    ilogger.info('changed_to_early_date', '{} {}->{}'.format(
                        get_admin_a_tag(portal_settings), expire_date_current, expire_date_response), log_to_cron=True)

            apply_root_data_function = getattr(portal_settings, apply_root_data_function_name, None)
            if callable(apply_root_data_function):
                apply_root_data_function(
                    portal_data=response_data,
                    expire_date_increased=expire_date_increased,
                    expire_date_initial=expire_date_current
                )

    return True
