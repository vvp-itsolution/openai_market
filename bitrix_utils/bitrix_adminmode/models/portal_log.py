from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models

from bitrix_utils.bitrix_adminmode.constants import DEFAULT_PORTAL_LOG_LIMIT
from its_utils.app_logger.models.abs_log_record import AbsLogRecord
from its_utils.app_logger.models import LogRecord
from its_utils.functions import datetime_to_string

if TYPE_CHECKING:
    from bitrix_utils.bitrix_auth.models import BitrixPortal
    from its_utils.app_logger.models import LoggedApp, LogRecord


class PortalLog(AbsLogRecord):
    portal = models.ForeignKey(
        'bitrix_auth.BitrixPortal',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    from its_utils.django_postgres_fuzzycount.fuzzycount import FuzzyCountManager
    objects = FuzzyCountManager()

    class Meta:
        index_together = 'app', 'portal'

    class Admin(LogRecord.Admin):
        list_display = 'portal', 'type', 'level', 'dt_with_seconds', 'tag_link', 'some_msg'
        list_display_links = list_display
        list_filter = 'app', 'level', 'type', 'portal'
        raw_id_fields = 'type', 'script', 'app', 'portal'

    def save(self, *args, **kwargs):
        is_new = not self.id

        super().save(*args, **kwargs)

        if is_new:
            self.clear_log(self.portal, self.app)

    @property
    def pretty_message(self):
        return (
            u'[{}][{}]({})({})({})\n'
            u'portal: {}\n'
            u'{}\n'
            u'{}'.format(
                self.type, self.get_level_display(), self.script, self.lineno, datetime_to_string(self.date_time),
                self.portal,
                self.message,
                self.exception_info
            )
        )

    def before_save(self):
        pass

    @classmethod
    def get_portal_log_limit(cls):
        return getattr(settings, 'PORTAL_LOG_LIMIT', DEFAULT_PORTAL_LOG_LIMIT)

    @classmethod
    def clear_log(cls, portal: 'BitrixPortal', app: 'LoggedApp'):
        """
        Удалить записи за переделами лимита портала
        https://b24.it-solution.ru/workgroups/group/421/tasks/task/view/7571/
        """

        portal_logs = cls.objects.filter(portal=portal, app=app)
        limit_records = portal_logs.order_by('-id')[:cls.get_portal_log_limit()]
        min_id = limit_records.aggregate(min_id=models.Min('id'))['min_id']
        if min_id:
            portal_logs.filter(id__lt=min_id).delete()
