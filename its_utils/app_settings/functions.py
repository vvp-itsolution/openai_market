def set_value(key, value):
    from its_utils.app_settings.models import KeyValue
    from settings import ilogger
    result = KeyValue.objects.filter(key=key).update(value=value)
    if not result:
        KeyValue.objects.create(key=key, value=value)
    ilogger.debug('set_value', "{}=>{}".format(key, value))
    return

def get_value(key):
    from its_utils.app_settings.models import KeyValue
    try:
        return KeyValue.objects.get(key=key).value
    except KeyValue.DoesNotExist:
        return None