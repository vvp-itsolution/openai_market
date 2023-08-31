# -*- coding: UTF-8 -*-

from django.http import HttpResponse


def xls_to_django_response(xls):

    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=export.xls'
    xls.save(response)
    return response
