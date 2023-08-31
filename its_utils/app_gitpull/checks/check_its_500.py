# -*- coding: UTF-8 -*-
from django.core.checks import register, Warning

import urls


@register()
def check_its_500(app_configs, **kwargs):
    from its_utils.app_error import urls as app_error_urls
    errors = []
    url_included = False
    for url in urls.urlpatterns:
        urlconf_module = getattr(url, 'urlconf_module', None)
        if urlconf_module == app_error_urls:
            url_included = True

    if not url_included:
        errors.append(
            Warning(
                'its/500 url is not included',
                hint=None,
                obj='Warning',
                id='%s.W001' % 'check_its_500',
            )
        )

    return errors
