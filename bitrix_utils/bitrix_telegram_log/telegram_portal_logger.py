from typing import Optional, List

from django.utils.functional import cached_property

from its_utils.app_logger.models import LogRecord
from its_utils.app_logger.its_logger import ItsLogger
from its_utils.app_logger.utils import log_levels
from bitrix_utils.bitrix_auth.models import BitrixPortal
from bitrix_utils.bitrix_telegram_log.models import PortalChat

from settings import ilogger


class TelegramPortalLoggerMixin:
    portal = NotImplemented  # type: BitrixPortal
    bx_app_names = NotImplemented  # type: List[str]
    status_max_frequency = 0

    @cached_property
    def portal_chat(self) -> Optional[PortalChat]:
        return PortalChat.objects.filter(
            portal=self.portal,
            app__name__in=self.bx_app_names,
        ).first()

    def is_chat_bound(self) -> bool:
        return bool(self.portal_chat and self.portal_chat.chat_id)

    def log_to_telegram(self, level: int, log_type: str, message: str, tag: str = None):
        if (
                not self.is_chat_bound() or
                self.portal_chat.get_required_level() > level or
                self.portal_chat.is_muted_log_type(log_type)
        ):
            return

        try:
            self.portal_chat.log(
                level=level,
                log_type=log_type,
                message=message,
                tag=tag,
            )

        except Exception as exc:
            ilogger.error(
                'telegram_portal_log_error',
                'failed to send record to telegram on portal {}: {}\n{} {}\n{}'.format(
                    self.portal, exc, level, log_type, message
                ),
            )

    def status(self, text: str) -> bool:
        if not self.is_chat_bound():
            return False

        return self.portal_chat.status(text=text, max_frequency=self.status_max_frequency)


class TelegramPortalLogger(ItsLogger, TelegramPortalLoggerMixin):
    def __init__(self, app, portal, record_model=LogRecord, bx_app_names=[], status_max_frequency=0, **kwargs):
        super().__init__(app=app, record_model=record_model, **kwargs)
        self.portal = portal
        self.bx_app_names = bx_app_names
        self.status_max_frequency = status_max_frequency

    def _write_log(self, log_type, message=None, *args, tag=None, add_rst=None, level=log_levels.INFO, **kwargs):
        result = super()._write_log(log_type, message, *args, tag=tag, add_rst=add_rst, level=level, **kwargs)
        self.log_to_telegram(level=level, log_type=log_type, message=message, tag=tag)
        return result
