# -*- coding: UTF-8 -*-

import xlwt


def query_to_xls(model, query=None, fields=None):

    if not query:
        query = {}

    if not fields:
        fields = model._meta.fields

    data = model.objects.filter(**query).select_related().values(*fields)

    xls = xlwt.Workbook()
    table = xls.add_sheet('New Sheet')

    for i, f in enumerate(fields):
        table.write(0, i, f)

    for i, row in enumerate(data, 1):
        for j, f in enumerate(fields):
            table.write(i, j, unicode(data[i-1][f]))

    return xls
