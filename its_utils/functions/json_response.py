# -*- coding: utf-8 -*-

import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse


def _dumps(*args, **kwargs):
    kwargs.setdefault('cls', DjangoJSONEncoder)
    return json.dumps(*args, **kwargs)


def json_resp(dict_, *args, **kwargs):
    kwargs['content_type'] = 'application/json'
    return HttpResponse(_dumps(dict_), *args, **kwargs)


def jsonp_resp(callback, dict_, *args, **kwargs):
    kwargs['content_type'] = 'text/javascript'
    return HttpResponse('%s(%s);' % (callback, _dumps(dict_)), *args, **kwargs)
