
def day_off(date=None):
    from django.utils import timezone
    if date==None:
        date = timezone.now()
    days_off_calendar = {"2015":{"1":{"1":{"isWorking":2},"2":{"isWorking":2},"5":{"isWorking":2},"6":{"isWorking":2},"7":{"isWorking":2},"8":{"isWorking":2},"9":{"isWorking":2}},"2":{"20":{"isWorking":3},"23":{"isWorking":2}},"3":{"6":{"isWorking":3},"9":{"isWorking":2}},"4":{"30":{"isWorking":3}},"5":{"1":{"isWorking":2},"4":{"isWorking":2},"8":{"isWorking":3},"11":{"isWorking":2}},"6":{"11":{"isWorking":3},"12":{"isWorking":2}},"11":{"3":{"isWorking":3},"4":{"isWorking":2}},"12":{"31":{"isWorking":3}}},"2016":{"1":{"1":{"isWorking":2},"4":{"isWorking":2},"5":{"isWorking":2},"6":{"isWorking":2},"7":{"isWorking":2},"8":{"isWorking":2}},"2":{"20":{"isWorking":3},"22":{"isWorking":2},"23":{"isWorking":2}},"3":{"7":{"isWorking":2},"8":{"isWorking":2}},"5":{"2":{"isWorking":2},"3":{"isWorking":2},"9":{"isWorking":2}},"6":{"13":{"isWorking":2}},"11":{"3":{"isWorking":3},"4":{"isWorking":2}}}}
    year = days_off_calendar.get(str(date.year), None)
    if year:
        month = year.get(str(date.month), None)
        if month:
            day = month.get(str(date.day), None)
            if day:
                return bool(day['isWorking'])
    return date.weekday() in [5, 6] and True or False
