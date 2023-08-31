from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils import timezone

from bitrix_utils.bitrix_auth.models import BitrixUserToken
from bitrix_utils.bitrix_robots import RobotBase
from its_utils.app_admin.action_admin import ActionAdmin
from its_utils.app_admin.json_admin import JsonAdmin
from settings import ilogger


class AbsRobotWaiter(models.Model):
    """Оффлайн-событие, полученное от Б24
    """
    BX_APPLICATION_CODE = 'unknown'


    portal = models.ForeignKey(verbose_name='битрикс-портал', to='bitrix_auth.BitrixPortal', on_delete=models.PROTECT,)
    # От имени какого пользователя выполняется активити
    user = models.ForeignKey(verbose_name='битрикс-пользователь', to='bitrix_auth.BitrixUser',on_delete=models.PROTECT)
    props = JSONField('параметры запроса из конструктора БП', null=True, blank=True)
    params = JSONField('параметры запроса', null=True, blank=True)
    queued = models.DateTimeField(verbose_name='добавлено в очередь', default=timezone.now, db_index=True,)
    # started = models.DateTimeField(verbose_name='начало обработки', default=None, null=True, blank=True, db_index=True,)
    processed = models.DateTimeField(verbose_name='обработано', null=True, blank=True, db_index=True,)

    return_values = JSONField('результат выполнения запроса', null=True, blank=True)
    error = JSONField('ошибка выполнения', null=True, blank=True)
    #has_error = models.BooleanField(default=False)

    class Meta:
        abstract = True
        #ordering = '-queued', '-pk',
        #index_together = [['bx_portal', 'processed']]
        #verbose_name = 'запрос'
        #verbose_name_plural = 'очередь запросов'

    class Admin(ActionAdmin, JsonAdmin):
        list_display = (
            'id', 'portal', 'user', 'queued', 'error'
        )
        raw_id_fields = ['portal', 'user']
        # list_display_links = list_display
        # list_select_related = 'bx_portal', 'bx_app',
        # list_filter = (
        #     'has_error', 'bx_app', 'activity',
        #     'queued', 'started', 'processed',
        # )
        # actions = "process",
        # search_fields = 'id', 'bx_portal__domain', 'props', 'activity', 'props__rest_method_name'
        # readonly_fields = 'queued', 'started', 'processed', 'result', 'error',

    def process(self):

        return NotImplemented

    def send_result(self):
        token = BitrixUserToken.get_random_token(self.BX_APPLICATION_CODE, self.portal_id, True)
        try:
            token.call_api_method('bizproc.event.send', dict(
                event_token=self.params['event_token'],
                return_values=RobotBase.fix_return_values(self.return_values),
            ))

        except Exception as exc:
            if getattr(exc, 'error', None) == 404:
                # процесс удалён
                pass
            else:

                ilogger.warning('robot_send_result_error', '{} at {}: {}'.format(
                    type(self).__name__, self.portal, exc
                ))

        self.processed = timezone.now()
        self.save()



    # def save(self, *args, **kwargs):
    #
    #     return super(AbsRobotWaiter, self).save(*args, **kwargs)

    # def __str__(self):
    #     return 'Запрос "{self.activity_name}" к {domain} {queued}'.format(
    #         self=self,
    #         domain=self.bx_portal.domain,
    #         queued=dateformat.format(self.queued, settings.DATETIME_FORMAT),
    #     )