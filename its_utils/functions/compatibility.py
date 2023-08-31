from django import VERSION as DJANGO_VERSION


def get_json_field():
    if DJANGO_VERSION[0] >= 4:
        from django.db.models import JSONField
    else:
        from django.contrib.postgres.fields import JSONField

    return JSONField


def get_null_boolean_field():
    if DJANGO_VERSION[0] >= 4:
        from django.db.models import BooleanField as NullBooleanField
    else:
        from django.db.models import NullBooleanField

    return NullBooleanField
