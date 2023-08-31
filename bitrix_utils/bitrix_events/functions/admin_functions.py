from urllib.parse import urlencode

from django.utils.safestring import mark_safe


def get_entity_redirect_urls_display(obj):
    return mark_safe(
        '<ul>'
        '<li><a href="{}" target="_blank">В админку</a></li>'
        '<li><a href="{}" target="_blank">В битрикс</a></li>'
        '<ul>'.format(
            get_entity_redirect_url(obj, to_admin=True),
            get_entity_redirect_url(obj)
        )
    )


def get_entity_redirect_url(obj, to_admin=False):
    params = dict(
        portal_id=obj.portal_id,
        model_name=obj._meta.model_name,
        app_label=obj._meta.app_label,
        bitrix_id=obj.bitrix_id
    )

    if to_admin:
        params['to_admin'] = 1

    return '/mirror/reflection_redirect/?{}'.format(urlencode(params))
