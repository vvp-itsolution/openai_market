from django.db import models
from django.utils import timezone

from its_utils.app_admin.get_admin_url import get_admin_a_tag
from its_utils.app_model.abs_locker_model import LockedTooLong, Locked, AbsLockerModel
from its_utils.app_timeit.timeit import TimeIt
from settings import ilogger


class NewActivityByIDMixin(models.Model, AbsLockerModel):
    # Применяется для наследников AbsPortalEventSetting
    # для сбора событий появляения новых дел по появлению нового ID

    # Для работы должнен быть метод get_bx_token()???

    # Написать action_admin
    # Написать админку
    # Локер поле
    # Поле хранилка

    nabid_lock_dt = models.DateTimeField(null=True, blank=True)
    nabid_last_check_dt = models.DateTimeField(null=True, blank=True)
    nabid_last_id = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True

    def collect_new_activities(self):

        # Здесь мы гарантируем запуск одного потока обработки для одного портала
        try:
            with self.lock_with_field('nabid_lock_dt'):
                with TimeIt() as ti:
                    res = self._collect_new_activities()
                return '{}: created - {} duration={:.3f} '.format(self.portal, res, ti.duration)
        except LockedTooLong:
            ilogger.warning(
                'collect_bitrix_events_new_flow_LockedTooLong',
                '{} failed to collect events objects on portal'
                    .format(get_admin_a_tag(self, self.portal))
            )
            return 'LockedTooLong'
        except Locked:
            return 'Locked'

    def _collect_new_activities(self):
        cls = self._meta.model  # Конкретный, а не абстрактный класс настроек

        bx_token = self.get_bx_token()
        last_id = self.nabid_last_id
        if not last_id:
            # Первый раз инициализируем последний id дела
            try:
                last_id = bx_token.call_api_method("crm.activity.list", {
                    'order': {"ID": 'desc'},
                    'select': ['ID']
                })['result'][0]['ID']
            except IndexError:
                last_id = 0
            cls.objects.filter(pk=self.pk).update(nabid_last_id=last_id)



        created_activities = bx_token.call_list_method("crm.activity.list", {
            'filter': {">ID": last_id},
            'select': ['ID']
        })

        from bitrix_utils.bitrix_telegram_log.telegram_portal_logger import TelegramPortalLogger
        TelegramPortalLogger(
            app='bpstarter',
            portal=self.portal,
            bx_app_names=['itsolutionru.bpstarter'],
        ).debug('collect_last_id_flow', f'ID>{last_id} {created_activities}')

        if created_activities:
            last_id = max([x["ID"] for x in created_activities])
            cls.objects.filter(pk=self.pk).update(nabid_last_id=last_id)

        cls.objects.filter(pk=self.pk).update(nabid_last_id=last_id, nabid_last_check_dt=timezone.now())

        return created_activities
