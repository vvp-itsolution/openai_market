# coding: utf-8
import json

from django.utils.module_loading import import_string

from its_utils.app_logger.its_logger import ItsLogger
from its_utils.app_settings.models import KeyValue
from its_utils.app_logger.models import LogRecord

DEFAULT_LAST_LOG_ID_KEY = 'APP_LOGGER_LAST_PROCESSED_LOG_RECORD_ID'


def process_log_records(last_log_id_key=DEFAULT_LAST_LOG_ID_KEY, record_model=LogRecord):
    """
    Отправить логи на почту

    :param last_log_id_key: ключ KeyValue, в которм хранится id последней обработанной записи
    :param record_model: модель, в которой хранятся записи
    """

    if record_model is str:
        record_model = import_string(record_model)

    last_log_key_value, _ = KeyValue.objects.get_or_create(key=last_log_id_key, defaults=dict(value=0))

    logger = ItsLogger(record_model=record_model)
    last_log_id, status = logger.process_logs(int(last_log_key_value.value))

    if last_log_id:
        last_log_key_value.value = last_log_id
        last_log_key_value.save()

    return json.dumps(status)
