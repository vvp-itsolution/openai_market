from typing import List

from its_utils.app_logger.utils import log_levels
from bitrix_utils.bitrix_telegram_log.telegram_portal_logger import TelegramPortalLoggerMixin
from bitrix_utils.bitrix_adminmode.portal_logger import PortalLogger


class TelegramPortalLoggerForAdminMode(PortalLogger, TelegramPortalLoggerMixin):
    def __init__(self, *args, bx_app_names: List[str], status_max_frequency=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.bx_app_names = bx_app_names
        self.status_max_frequency = status_max_frequency

    def _write_log(self, log_type, message=None, *args, tag=None, add_rst=None, level=log_levels.INFO, **kwargs):
        result = super()._write_log(log_type, message, *args, tag=tag, add_rst=add_rst, level=level, **kwargs)
        self.log_to_telegram(level=level, log_type=log_type, message=message, tag=tag)
        return result
