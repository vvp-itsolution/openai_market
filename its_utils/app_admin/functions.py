try:
    from prettyjson import PrettyJSONWidget
except:
    PrettyJSONWidget = None

try:
    from django.db.models import JSONField
except:
    JSONField = None

try:
    from django.contrib.postgres.fields import JSONField as PostgresJSONField
except:
    PostgresJSONField = None


def override_json_form_field(admin_cls):
    if PrettyJSONWidget:
        if JSONField:
            admin_cls.formfield_overrides.setdefault(
                JSONField, {'widget': PrettyJSONWidget},
            )

        if PostgresJSONField:
            admin_cls.formfield_overrides.setdefault(
                PostgresJSONField, {'widget': PrettyJSONWidget},
            )
