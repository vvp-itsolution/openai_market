from its_utils.app_logger.models import LogType


def clean_logs():
    results = []
    for log_type in LogType.objects.filter(storage_days__isnull=False):
        results.append(
            '{}: {}'.format(log_type.name, log_type.clean_logs())
        )

    return '\n'.join(results)