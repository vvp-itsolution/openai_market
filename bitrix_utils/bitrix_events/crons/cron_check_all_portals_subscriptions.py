# coding=utf-8

from __future__ import unicode_literals

from integration_utils.bitrix24.functions.api_call import BitrixTimeout
from bitrix_utils.bitrix_auth.models.bitrix_user_token import \
    BitrixUserTokenDoesNotExist, BitrixApiError, BitrixApiServerError
from settings import ilogger
from django.utils.module_loading import import_string


def cron_check_all_portals_subscriptions(class_path=None):
    """
    Порверить подписки на события для всех порталов
    class_path = 'event_collector.models.portal_events_setting.PortalEventSetting'

    """
    if not class_path:
        raise Exception('Не указан class_path')

    SettingsClass = import_string(class_path)

    portals_settings = SettingsClass.objects.filter(is_active=True)
    fails = 0

    results = []
    for portal_setting in portals_settings:
        try:
            res = portal_setting.subscribe_on_events()
            results.append('{}: {} subs, {} unsubs, {} untouched'.format(
                portal_setting.portal,
                len(res['bind'].successes),
                len(res['unbind'].successes),
                len(res['untouched']),
            ))

        except BitrixUserTokenDoesNotExist as ex:
            fails += 1
            ilogger.info('tokens_not_found', '{!r}'.format(ex))
        except BitrixTimeout:
            fails += 1
        except BitrixApiServerError:
            fails += 1
        except BitrixApiError as e:
            fails += 1
        except:
            # Тут может быть наш косяк, так что log_lvl error
            ilogger.error('events_check_subscriptions_bitrix_error', 'error')

    results.append('----------')
    results.append('fails: {}'.format(fails))

    return '\n'.join(results)
