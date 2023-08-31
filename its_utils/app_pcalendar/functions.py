from django.utils import timezone

from its_utils.app_pcalendar.calendar_work_days import WORK_AND_REST_DAYS


def is_work_day(date=None):
    from django.utils import timezone
    if date is None:
        date = timezone.now()
    day_type = WORK_AND_REST_DAYS.get((date.year, date.month, date.day), None)
    if day_type is not None:
        return day_type

    if date.weekday() in [5, 6]:
        return False
    else:
        return True


def work_days_diff(dt, days):
    # Функция перелистывающая рабочии дни, как сутки назад, но ищет именно рабочий день
    # Есди сегодня понедельник, то один рабочий день назад это пятница
    # А если сегодня суббота????? то скорее тоже пятница
    while days:
        if days > 0:
            dt = dt + timezone.timedelta(hours=24)
        else:
            dt = dt - timezone.timedelta(hours=24)
        if is_work_day(dt):
            if days > 0:
                days -= 1
            else:
                days += 1

    return dt