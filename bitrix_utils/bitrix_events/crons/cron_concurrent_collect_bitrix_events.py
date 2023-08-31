# coding=utf-8
from __future__ import unicode_literals

from django.utils import timezone
from django.utils.module_loading import import_string

from its_utils.app_timeit.timeit import TimeIt
from settings import ilogger


def cron_concurrent_collect_bitrix_events(class_path=None, limit=30, max_workers=15, force=True):
    """
    Получить новые события на порталах и сохранить их в модель BitrixEvent
    force = Брать порталы в которых не вытащили все события
    limit = Сколько в очередь набирать порталов, не все обработаются из-за параллельности
    max_workers = Количество потоков обработки
    """

    if not class_path:
        raise Exception('Не указан class_path')

    ilogger.debug('collect_events_enter', 'enter to function', log_to_cron=True)

    SettingsClass = import_string(class_path)

    results = []

    qs = SettingsClass.objects.filter(is_active=True)
    qs_plan = qs.filter(last_collect_events__lt=timezone.now() - timezone.timedelta(seconds=SettingsClass.FREQUENCY)) # Если обновляли меньше чем FREQUENCY секунд назад, то не пытаемся обновлять)
    qs_force = qs.filter(force_collect_events=True)
    qs = qs_force | qs_plan

    import concurrent.futures

    ilogger.info('collect_events', 'to proceess {}'.format(qs.count()), log_to_cron=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_notify = [executor.submit(ps.collect_bitrix_events) for ps in qs]
        concurent_results = concurrent.futures.as_completed(future_notify)
        for cr in concurent_results:
            results.append(cr.result())

    return '\n'.join(results)
