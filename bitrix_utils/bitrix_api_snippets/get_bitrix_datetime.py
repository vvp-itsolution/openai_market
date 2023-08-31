from datetime import timedelta

from django.utils import timezone


def get_bitrix_datetime(datetime):
    # Возвращает дату для использования в REST API
    # '2017-02-01T21:30:05+03:00'
    #

    return datetime.isoformat()


def days_ago(days):
    date = timezone.now() - timedelta(days=days)
    return get_bitrix_datetime(date)

def yesterday():
    # evg_at_b24_token.call_list_fast('crm.deal.list', {'filter':{'>DATE_MODIFY':yesterday()}}))

    date = timezone.now()-timedelta(days=-1)
    return get_bitrix_datetime(date)