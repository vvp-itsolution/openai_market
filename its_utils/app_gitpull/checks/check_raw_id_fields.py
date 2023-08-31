# -*- coding: UTF-8 -*-

from django.core.checks import Warning, register

from its_utils.app_gitpull import gitpull_settings

from its_utils.functions2.get_models import get_models, get_model_fields

MAX_ALLOWABLE_RECORDS_COUNT = 50

APPS_TO_CHECK = gitpull_settings.APPS_TO_CHECK


@register()
def check_raw_id_fields(app_configs, **kwargs):
    from django.contrib import admin

    from django.db import models

    errors = []

    for app_name in APPS_TO_CHECK:
        if '.' in app_name:
            _, app_name = app_name.rsplit('.', 1)

        app_models = get_models(app_name)

        for model in app_models:
            try:
                admin_cls = admin.site._registry[model]
            except KeyError:
                continue
            raw_id_fields = admin_cls.raw_id_fields
            autocomplete_fields = getattr(admin_cls, 'autocomplete_fields', ())

            foreign_key_fields = []
            for field in get_model_fields(model):
                if not isinstance(field, models.ForeignKey):
                    continue
                if field.name in raw_id_fields:
                    continue
                if field.name in autocomplete_fields:
                    continue
                # Выводить предупреждение, если количестве записей во внешней таблице больше 50
                records_count = field.related_model.objects.all().count()
                if records_count <= MAX_ALLOWABLE_RECORDS_COUNT:
                    continue

                foreign_key_fields.append(field.name)

            if foreign_key_fields:
                errors.append(
                    Warning(
                        'Not all foreign fields are '
                        'raw_id_fields/autocomplete_fields in admin for model '
                        '{app}.{model}: {fields}'.format(
                            app=app_name,
                            model=model._meta.object_name,
                            fields=foreign_key_fields,
                        ),
                        hint=None,
                        obj='Warning',
                        id='%s.W001' % app_name,
                    )
                )

    return errors
