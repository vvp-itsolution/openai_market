# -*- coding: UTF-8 -*-

from django.core.checks import Warning, register
from its_utils.app_gitpull import gitpull_settings

from its_utils.functions2.get_models import get_models, get_model_fields

APPS_TO_CHECK = gitpull_settings.APPS_TO_CHECK


@register()
def check_on_delete_protect(app_configs, **kwargs):
    from django.db import models

    errors = []

    for name in APPS_TO_CHECK:
        try:
            name = name.split('.')[1]
        except IndexError:
            pass

        app_models = get_models(name)
        for model in app_models:
            for field in get_model_fields(model):
                if isinstance(field, models.ForeignKey):
                    rel = getattr(field, 'rel', getattr(field, 'remote_field', None))
                    if rel and rel.on_delete != models.PROTECT:
                        errors.append(
                            Warning(
                                'ForeignKey field "%s.%s" has no on_delete=PROTECT property' % (
                                    model._meta.object_name, field.name
                                ),
                                hint=None,
                                obj='Warning',
                                id='%s.W001' % name,
                            )
                        )
    return errors
