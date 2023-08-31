# -*- coding: utf-8 -*-
import datetime

import dateutil.parser
import six


from django.db import models
try:
    from django.db.models import JSONField
except:
    from django.contrib.postgres.fields import JSONField
from django.http import \
    HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from integration_utils.bitrix24.functions.api_call import BitrixTimeout
from bitrix_utils.bitrix_auth.functions.dec_bitrix_start_point import \
    bitrix_start_point_process
from bitrix_utils.bitrix_auth.models import BitrixPortal
from bitrix_utils.bitrix_auth.models.bitrix_user_token import \
    BitrixApiError, BitrixUserToken, BitrixUserTokenDoesNotExist
from its_utils.app_admin.action_admin import ActionAdmin

from its_utils.app_admin.get_admin_url import \
    get_admin_a_tag
from its_utils.app_admin.json_admin import JsonAdmin
from its_utils.app_jsonfield_update.jsonfield_update import jsonfield_update
from its_utils.app_model.abs_locker_model import \
    AbsLockerModel, Locked, LockedTooLong
from its_utils.app_timeit.timeit import TimeIt

from settings import ilogger


class CollectEventsLocked(Exception):
    pass


class CollectEventsLockedTooLong(Exception):
    pass


@six.python_2_unicode_compatible
class AbsPortalEventSetting(models.Model, AbsLockerModel):

    ERROR_DESCRIPTION_ALREADY_BINDED = "already binded"
    EVENT_LIST = None  # список событий для подписки List[str]
    ONLINE_ONLY_EVENT_LIST = []  # Список событий, которые обрабатываются только онлайн. логику обработки нужно определить самостоятельно в методе handle_online_event
    NOT_MANAGED_EVENT_LIST = [] #Список событий которые мы не хотим подписывать и отписывать, например для использования в другой части приложения
    EVENT_MODEL = None  # Модель события, потомок AbsBitrixEvent
    APPLICATION_NAME = None
    FREQUENCY = 60 # частота сбора событий по крону
    # URL онлайн-обработчика
    # NB! Если событий много, онлайн-обработчик может быть не нужен,
    # не устанавливайте его в этом случае или явно укажите None.
    # Пример:
    #     BITRIX_ONLINE_EVENT_HANDLER = 'https://mirror3.it-solution.ru/event_collector/event_handler/'
    # Еще пример, urls.py:
    #     urlpatterns = [
    #         path('bitrix_events/', include(MyPortalSettings.urls())),
    #     ]
    # models/my_app/my_portal_settings.py
    #     class MyPortalSettings(AbsPortalEventSetting):
    #         BITRIX_ONLINE_EVENT_HANDLER = 'https://my-app-domain.ru/bitrix_events/event_handler/'
    BITRIX_ONLINE_EVENT_HANDLER = None

    portal = models.OneToOneField('bitrix_auth.BitrixPortal', on_delete=models.PROTECT)

    lock_dt_for_collect_events = models.DateTimeField('Время взятия в обработку', null=True, blank=True)
    force_collect_events = models.BooleanField('Запустить принудительно сбор событий', default=False, db_index=True)
    remaining_number = models.IntegerField('Осталось собрать событий', default=0, null=True)
    today_events_count = models.IntegerField('Событий за сегодня', default=0, null=True)
    last_collect_events = models.DateTimeField('Время последнего получения событий', blank=True, default=timezone.now, db_index=True)

    data = JSONField('Дополнительные данные', default=dict, blank=True)

    force_offline_event_list = models.TextField('Офлайн события портала', blank=True, null=True, help_text='Портал будет подписан только на эти Офлайн события')
    force_online_event_list = models.TextField('Онлайн события портала', blank=True, null=True, help_text='Портал будет подписан только на эти онлайн события')
    registered_events = models.TextField('Зарегистрированные подписки', blank=True, null=True, editable=False)


    install_date = models.DateTimeField('дата-время установки', default=timezone.now, null=True)

    # Указывает на необходимость сбора событий при обработке
    is_active = models.BooleanField('собирать события', default=True)

    class Meta:
        abstract = True
        verbose_name = u'Настройки портала (для сбора событий)'
        verbose_name_plural = u'Настройки порталов (для сбора событий)'

    class Admin(ActionAdmin, JsonAdmin):
        list_display = (
            'portal', 'remaining_number', 'today_events_count', 'lock_dt_for_collect_events', 'force_collect_events',
            'last_collect_events', 'install_date', 'is_active'
        )
        list_display_links = list_display
        list_filter = ['force_collect_events']
        search_fields = ['portal__domain']
        actions = ['collect_bitrix_events', 'subscribe_on_events', 'unsubscribe_from_all_events']
        readonly_fields = 'registered_events',

    def __str__(self):
        return self.portal.domain

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.APPLICATION_NAME:
            raise Exception('APPLICATION_NAME not presented')
        if not self.EVENT_LIST:
            raise Exception('EVENT_LIST is empty')
        if not self.EVENT_MODEL:
            raise Exception('EVENT_MODEL unknown')

    def get_bx_token(self):
        # type: () -> BitrixUserToken

        return BitrixUserToken.get_random_token(
            application_name=self.APPLICATION_NAME,
            portal_id=self.portal_id,
        )

    @classmethod
    def get_for_portal(cls, portal):
        # type: (BitrixPortal) -> AbsPortalEventSetting

        """
        Вызывается при каждом входе в приложение
        """

        return cls.objects.get_or_create(portal=portal)[0]

    def collect_bitrix_events(self, timeout=5):
        """Получение оффлайн событий из bitrix
        https://dev.1c-bitrix.ru/learning/course/?COURSE_ID=99&LESSON_ID=4462&LESSON_PATH=8771.5380.2461.4462

        :returns: строка с описанием результата
        """
        try:
            with self.lock_for_collect_events():
                with TimeIt() as ti:
                    res = self._collect_bitrix_events(timeout=timeout)
                return '{}: {} duration={:.3f}'.format(self.portal, res, ti.duration)
        except LockedTooLong:
            ilogger.warning(
                'collect_bitrix_events_LockedTooLong',
                '{} failed to collect events objects on portal'
                .format(get_admin_a_tag(self, self.portal))
            )
            return 'LockedTooLong'
        except Locked:
            return 'Locked'

    def _collect_bitrix_events(self, timeout):
        """см. collect_bitrix_events"""

        force_collect_events = False
        remaining_number = self.remaining_number
        cls = self._meta.model  # Конкретный, а не абстрактный класс настроек
        events = []

        try:
            bx_token = self.get_bx_token()
            ilogger.debug('collect_bitrix_events', 'start for {}'.format(self.portal.domain))

            result = bx_token.call_api_method('event.offline.list', timeout=timeout, log_prefix='cbe__')
            events = result['result']

            ilogger.debug('collect_bitrix_events', 'got {} events; total events in queue: {}'.format(
                len(events), result.get('total', 0)
            ))

            message_ids = []
            for event in events:
                ilogger.debug('collect_bitrix_events', '{} got events'.format(event['EVENT_NAME']))

                if event['EVENT_NAME'] in self.ONLINE_ONLY_EVENT_LIST:
                    # событие не должно обрабатываться офлайн
                    message_ids.append(event['ID'])
                    continue

                # Записать событие в бд
                try:
                    # Предпочтительно знать время совершения события на портале,
                    # а не появления его в нашей базе
                    event_dt = dateutil.parser.isoparse(event['TIMESTAMP_X'])
                except (KeyError, ValueError):
                    ilogger.error('event_no_or_bad_timestamp', repr(event))
                    event_dt = timezone.now()
                self.EVENT_MODEL.objects.create(
                    portal=self.portal, event_name=event['EVENT_NAME'],
                    data=event, datetime=event_dt)

                message_ids.append(event['ID'])

            if message_ids:
                # вычищаем очередь от обработанных событий
                bx_token.call_api_method('event.offline.clear', {'process_id': '', 'id': message_ids}, log_prefix='cbe__')

            ilogger.debug('collect_bitrix_events', 'finished for {}'.format(self.portal.domain))

            force_collect_events = result.get('total', 0) > 50
            remaining_number = max(result.get('total', 0)-50, 0)

            result = 'collected {}, total {}'.format(len(events), result.get('total', "unknown"))

        except BitrixTimeout as e:
            ilogger.warning(
                'collect_bitrix_events_timeout',
                'TIMEOUT portal: {portal}, timeout: {err!r}\n{link}'
                .format(portal=self.portal, err=e,
                        link=get_admin_a_tag(self, self.portal)),
                exc_info=True,
            )
            result = 'timeout'
        except BitrixUserTokenDoesNotExist:
            # Закомментировал, т.к в бпстартере порталы деактивировались, но потом им нечем обратно активироваться
            # cls.objects.filter(pk=self.pk).update(is_active=False)
            # ilogger.warning('portal_settings_deactivated', '{}'.format(get_admin_url(self)))
            result = 'no token'

        except BitrixApiError as e:
            if e.is_internal_server_error:
                result = 'connection error'
            elif e.is_error_connecting_to_authorization_server:
                result = 'error_connecting_to_authorization_server'
            elif e.is_error_connecting_to_authorization_server:
                result = 'error_connecting_to_authorization_server'
            elif e.is_connection_to_bitrix_error:
                result = 'connection_to_bitrix_error'
            elif e.is_license_check_failed:
                result = 'is_license_check_failed'
            elif e.is_no_auth_found:
                result = 'no auth found'
            elif e.is_portal_deleted:
                result = 'is_portal_deleted'
            elif e.is_free_plan_error:
                result = 'is_free_plan_error'
            elif e.is_wrong_encoding:
                result = 'is_wrong_encoding'
            elif e.is_authorization_error:
                result = 'is_authorization_error'
            elif e.is_out_of_disc_space_error:
                result = 'is_out_of_disc_space_error'
            elif e.is_status_gte_500:
                result = 'is_status_gte_500'
            elif e.is_application_not_found:
                result = 'application_not_found'
            else:
                ilogger.error(
                    'collect_bitrix_events',
                    '{} bitrix api error'
                    .format(get_admin_a_tag(self, self.portal))
                )
                result = 'bitrix api error'

        except Exception:
            ilogger.error(
                'collect_bitrix_events',
                '{} failed to collect events objects on portal'
                .format(get_admin_a_tag(self, self.portal))
            )
            result = 'unknown error'

        # Записываем количество событий в json field data, может пригодиться для учета и ограничений
        pes = cls.objects.get(pk=self.pk)
        counter = pes.data.get('events_counter', {})
        counter[str(datetime.date.today())] = counter.get(str(datetime.date.today()), 0) + len(events)
        jsonfield_update(pes, 'data', 'events_counter', counter)

        cls.objects.filter(pk=self.pk).update(
            force_collect_events=force_collect_events,
            remaining_number=remaining_number,
            last_collect_events=timezone.now(),
            today_events_count=counter[str(datetime.date.today())])




        return result

    def unsubscribe_from_all_events(self):
        """
        Отписаться от всех событий

        :return: результат batch-вызова отписки
        """

        bx_token = self.get_bx_token()

        # Активные подписки
        subs = bx_token.call_api_method('event.get')['result']

        # Собираем методы для батч-запроса
        methods = []
        for sub in subs:
            event = sub['event']
            event_type = 'offline' if sub.get('offline') else 'online'
            handler = sub.get('handler') if sub.get('handler') else 'offline'

            methods.append((
                '{}:{}'.format(event, event_type),
                'event.unbind',
                dict(event=event, event_type=event_type, handler=handler)
            ))

        # Отписываемся сразу от всех и возвращаем результат отписки
        return bx_token.batch_api_call(methods)

    def _get_portal_event_plan(self):
        if self.data.get('event_plan'):
            event_list = self.data.get('event_plan')
        else:
            event_list = self.EVENT_LIST

        if self.force_offline_event_list:
            offline_events = [e.strip() for e in self.force_offline_event_list.split(',')]
        else:
            offline_events = list(set(event_list) - set(self.ONLINE_ONLY_EVENT_LIST))

        if self.force_online_event_list:
            online_events = [e.strip() for e in self.force_online_event_list.split(',')]
        else:
            online_events = list(event_list)

        return offline_events, online_events

    def get_online_event_handler(self):
        if not self.BITRIX_ONLINE_EVENT_HANDLER:
            return None

        return '{}?portal_id={}'.format(self.BITRIX_ONLINE_EVENT_HANDLER, self.portal_id)

    def subscribe_on_events(self, bx_token=None):
        """
        Подписаться на события и отписаться от более не нужных

        :rtype: dict
        :returns: {
            # Результат батч-подписки
            'bind': {
                'ONCRMACTIVITYADD:online': {
                    'result': True,
                    'error': None,
                },
                'ONCRMACTIVITYUPDATE:offline': {...},
                ...
            },
            # Результат батч-отписки
            'unbind': {
                'ONCRMACTIVITYDELETE:offline': {
                    'result': True,
                    'error': None,
                },
                ...
            },
            # Уже были активными и остались такими
            'untouched': {
                'ONCRMACTIVITYADD:offline': {
                    'event': 'ONCRMACTIVITYADD',
                    'offline': 1,
                    ...,
                },
            },
        }
        """

        # Получаем токен и активные подписки
        if bx_token is None:
            bx_token = self.get_bx_token()
        active_subs_result = bx_token.call_api_method('event.get')['result']

        # Определяем тип подписок и собираем в множество кортежей:
        # {(событие, 'offline'/'online', 'https://...'/'offline'), ...}
        active_subs_map = {}
        already_subscribed_events = set()
        for sub in active_subs_result:
            event_type = 'offline' if sub.get('offline') else 'online'
            handler = sub.get('handler') if sub.get('handler') else 'offline'

            already_subscribed_events.add((sub['event'], event_type, handler))

            event_key = '{}:{}'.format(sub['event'], event_type)
            active_subs_map[event_key] = sub

        # События на которые мы хотим быть подписаны
        if not self.is_active:
            # Не хотим собирать события, отпишемся от всего
            active_events = set()
        else:
            active_events = set()
            online_handler = self.get_online_event_handler()

            offline_events, online_events = self._get_portal_event_plan()

            for event in offline_events:
                active_events.add((event, 'offline', 'offline'))

            if online_handler is not None:
                # Подписка на онлайн-протакиватель
                # только при заданном обработчике
                for event in online_events:
                    active_events.add((event, 'online', online_handler))

        # Должны быть подписаны на эти события, но пока не подписались
        to_subscribe = set(active_events) - set(already_subscribed_events)
        # Левые подписки, отписываемся
        to_unsubscribe = set(already_subscribed_events) - set(active_events)

        # Уже активные нужные подписки, не отписываемся от них
        untouched = {}
        for event, event_type, handler in \
                set(already_subscribed_events) - to_unsubscribe:
            event_key = '{}:{}'.format(event, event_type)
            untouched[event_key] = active_subs_map[event_key]

        # Отписка от лишних событий
        methods = []
        for event, event_type, handler in to_unsubscribe:
            if event in self.NOT_MANAGED_EVENT_LIST:
                continue
            methods.append((
                '{}:{}'.format(event, event_type),
                'event.unbind',
                dict(event=event, event_type=event_type, handler=handler)
            ))
        unbind_result = bx_token.batch_api_call(methods)
        if not unbind_result.all_ok:
            ilogger.error('unbind_error', 'unbind_result: %r' % unbind_result)

        # Подписка на недостающие события
        methods = []
        for event, event_type, handler in to_subscribe:
            methods.append((
                '{}:{}'.format(event, event_type),
                'event.bind',
                dict(event=event, event_type=event_type, handler=handler)
            ))
        bind_result = bx_token.batch_api_call(methods)
        if not bind_result.all_ok:
            ilogger.error('bind_error', 'bind_result: %r' % bind_result)

        registered_events = list(untouched.keys()) + list(bind_result.successes.keys())
        self.registered_events = ', '.join(registered_events)
        self.save(update_fields=['registered_events'])

        # Информация о выполненных действиях
        return dict(
            bind=bind_result,
            unbind=unbind_result,
            untouched=untouched,
        )

    @classmethod
    @csrf_exempt
    def index(cls, request):
        bitrix_start_point_process(settings_name=None, request=request)
        ps = cls.get_for_portal(portal=request.bx_portal)
        ps.subscribe_on_events()
        return HttpResponse('Запуск удачный')

    @classmethod
    @csrf_exempt
    def online_event_handler(cls, request):
        """Обработка онлайн-событий.

        Основным механизмом получения событий является оффлайн-подписка:
        периодически порталы опрашиваются на предмет накопившихся событий.
        Такой способ надежнее онлайн событий, т.к. онлайн-события могут теряться.

        Однако онлайн события хороши тем, что они прихдят сразу
        (не надо ждать пока обработчик решит проверить события на данном портале)

        Решение: онлайн события для портала просто ставят порталу флаг приоритетной
        обработки, чтобы обработчик быстрее забрал события с этого портала.

        Пример POST-данных, передаваемых в запрос: {
            'auth[access_token]': 'a25e025d003d5210003cfe0200000001000003e7fcd7b32dded766fb4b2ecd8d919775',
            'auth[application_token]': '795dcf7fc3078917bbbe811cf8c4cac9',
            'auth[client_endpoint]': 'https://b24-foobar.bitrix24.com/rest/',
            'auth[domain]': 'b24-foobar.bitrix24.com',
            'auth[expires]': '1560436386',
            'auth[expires_in]': '3600',
            'auth[member_id]': 'd77ddce941c3b4ad340eb90ab42fbd0c',
            'auth[scope]': 'crm,bizproc,user',
            'auth[server_endpoint]': 'https://oauth.bitrix.info/rest/',
            'auth[status]': 'L',
            'auth[user_id]': '1',
            'data[FIELDS][ID]': '16',
            'event': 'ONCRMACTIVITYADD',
            'ts': '1560432785'
        }
        """
        try:
            portal_member_id = request.POST['auth[member_id]']
            application_token = request.POST['auth[application_token]']
            access_token = request.POST['auth[access_token]']
        except KeyError:
            return HttpResponseBadRequest('bad request')

        # Проверка подлинности события
        try:
            portal = BitrixPortal.objects.get(member_id=portal_member_id)
        except BitrixPortal.DoesNotExist:
            return HttpResponseForbidden('portal not found: member_id %s' % portal_member_id)
        if not portal.verify_online_event(
                application_name=cls.APPLICATION_NAME,
                access_token=access_token,
                application_token=application_token,
        ):
            return HttpResponseForbidden('forbidden')

        # бамп флага приоритетности обработки
        cls.objects \
            .filter(portal__member_id=portal_member_id) \
            .update(force_collect_events=True)

        cls.handle_online_event(portal, request)
        return HttpResponse('queued')

    @classmethod
    def handle_online_event(cls, portal, request):
        """
        Метод на случай, если нужна какая-то обработка онлайн-события, кроме обновления force_collect_events
        Вызывается из online_event_handler
        """
        pass

    @classmethod
    def urls(cls):
        from django.urls import path
        return [
            path('', cls.index),
            path('event_handler/', cls.online_event_handler)
        ]

    def lock_for_collect_events(self):
        return self.lock_with_field('lock_dt_for_collect_events')
