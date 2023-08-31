# -*- coding: utf-8 -*-
import functools

from django.http import JsonResponse, Http404
from django.http.response import HttpResponseBase

from settings import ilogger


def _response(content, **kwargs):
    kwargs.setdefault('safe', False)
    return JsonResponse(content, **kwargs)


def api_view(view_fn):
    @functools.wraps(view_fn)
    def decorated_view(request, *args, **kwargs):
        status = 200
        try:
            response = view_fn(request, *args, **kwargs)
        except Http404:
            raise
        except Exception as e:
            err_type = 'api_500_{}'.format(e.__class__.__name__)
            ilogger.error(err_type, repr(e), exc_info=True)
            response = dict(error='Internal server error'), 500
        if isinstance(response, tuple):
            response, status = response
        if not isinstance(response, HttpResponseBase):
            return _response({
                'result' if status < 400 else 'error': response,
            }, status=status)
        return response
    return decorated_view
