from bitrix_utils.bitrix_adminmode.models import PortalLog
from its_utils.app_logger.its_logger import ItsLogger


class PortalLogger(ItsLogger):
    def __init__(self, app, portal, record_model=PortalLog, **kwargs):
        super().__init__(app=app, record_model=record_model, **kwargs)
        self.portal = portal

    def make_log_record(self, **kwargs):
        record_fields = dict(portal=self.portal)
        record_fields.update(**kwargs)
        return self.record_model(**record_fields)
