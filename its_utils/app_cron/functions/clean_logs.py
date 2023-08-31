from its_utils.app_cron.models import Cron, CronResult
from its_utils.functions import is_date_in_cronstring
from django.utils import timezone
import threading


CLEAN_LOGS_CRON_STRING = '0 2 * * *'

def clean_logs():
    for cron in Cron.objects.all():
        results_for_this_cron_query = CronResult.objects.filter(cron=cron).order_by('-id')
        cron_results_to_keep = results_for_this_cron_query[:1000].values_list("id", flat=True)
        oldest_id_to_keep = cron_results_to_keep[len(cron_results_to_keep) - 1]
        results_for_this_cron_query.filter(id__lt=oldest_id_to_keep).delete()

def check_datetime_and_clean_logs(datetime=None):
    from django.conf import settings

    cleaning_needed = getattr(settings, 'CLEAN_CRON_LOGS', True)

    if cleaning_needed:

        if datetime is None:
            datetime = timezone.now()

        clean_logs_cron_string = CLEAN_LOGS_CRON_STRING

        settings_cron_string = getattr(settings, 'CLEAN_LOGS_CRON_STRING', '')
        if settings_cron_string:
            clean_logs_cron_string = settings_cron_string

        if is_date_in_cronstring(datetime, clean_logs_cron_string):
            threading.Thread(target=clean_logs, args=[]).start()