# -*- coding: UTF-8 -*-
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

import django

if django.VERSION[0] < 2:
    from django.core.urlresolvers import reverse, NoReverseMatch
else:
    from django.urls import reverse


def get_admin_a_tag(obj, text=None):
    if not text:
        try:
            text = obj.__str__()
        except:
            text = 'ссылка'

    return '<a href="{}">{}</a>'.format(get_admin_url(obj), text)


def get_admin_url(obj):
    if not obj:
        return 'https://url404'

    content_type = ContentType.objects.get_for_model(obj.__class__)
    # try:
    #     result = reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(obj.id,))
    # except NoReverseMatch:
    #     # Урл ресорвер гонит в кроне, я сделал ручками, но в будущем можно поразбиратсья хотя....
    #     # так вроде проще
    #     result = "/admin/{}/{}/{}/change/".format(
    #         content_type.app_label,
    #         content_type.model,
    #         obj.id
    #     )

    result = "/admin/{}/{}/{}/change/".format(
            content_type.app_label,
            content_type.model,
            obj.pk
        )

    try:
        if settings.DOMAIN:
            result = 'https://{}{}'.format(settings.DOMAIN, result)
    except AttributeError:
        pass

    return result


def get_admin_list_url(obj):
    content_type = ContentType.objects.get_for_model(obj.__class__)
    # try:
    #     result = reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(obj.id,))
    # except NoReverseMatch:
    #     # Урл ресорвер гонит в кроне, я сделал ручками, но в будущем можно поразбиратсья хотя....
    #     # так вроде проще
    #     result = "/admin/{}/{}/{}/change/".format(
    #         content_type.app_label,
    #         content_type.model,
    #         obj.id
    #     )

    result = "/admin/{}/{}/".format(
            content_type.app_label,
            content_type.model,
        )

    try:
        if settings.DOMAIN:
            result = 'https://{}{}'.format(settings.DOMAIN, result)
    except AttributeError:
        pass

    return result