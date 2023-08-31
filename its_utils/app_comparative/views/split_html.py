# -*- coding: utf-8 -*-
import requests
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.utils.html import escape

from its_utils.app_comparative.functions.diff import html2list


def split(request):

    url = request.GET.get('url', 0)
    if not url:
        return HttpResponseBadRequest("url not provided")

    html = requests.get(url).content.decode('utf-8')
    res = html2list(html)

    res_html = u''
    # num_line = 0
    for s in res:
        s = escape(s).replace('\n', '').replace('\r', '').replace('\t', '')

        if len(s) > 1:
            # num_line += 1
            # res_html += str(num_line) + '. ' + s + '\n'
            res_html += s + '\n'

    return HttpResponse('<pre>' + res_html + '</pre>')
