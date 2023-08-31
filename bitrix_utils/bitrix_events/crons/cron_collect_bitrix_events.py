# coding=utf-8
from __future__ import unicode_literals

from django.utils.module_loading import import_string

from its_utils.app_timeit.timeit import TimeIt


def cron_collect_bitrix_events(class_path=None, limit=10, force=True):
    """
    Получить новые события на порталах и сохранить их в модель BitrixEvent
    force = Брать порталы в которых не вытащили все события
    limit = Сколько в очередь набирать порталов, не все обработаются из-за параллельности
    """

    if not class_path:
        raise Exception('Не указан class_path')

    SettingsClass = import_string(class_path)

    results = []

    qs = SettingsClass.objects.filter(is_active=True)
    if force:
        qs = qs.order_by("-force_collect_events", "last_collect_events")
    else:
        qs = qs.order_by("last_collect_events")
    qs = qs[:limit]

    for ps in qs:
        # Получить события из очереди
        with TimeIt() as ti:
            res = ps.collect_bitrix_events()
        results.append(
            '{}: {} duration={:.3f}'.format(ps.portal, res, ti.duration)
        )
    return '\n'.join(results)
