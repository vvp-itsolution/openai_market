# -*- coding: utf-8 -*-
import difflib

import requests
from django.http import HttpResponse
from django.shortcuts import render

from its_utils.app_comparative.functions.diff import html2list, text_diff
from its_utils.app_comparative.models import Compared
from its_utils.app_comparative.models import Snippet


def compare(request, record_id):
    diffs = Compared.objects.get(id=record_id).compare()

    for diff in diffs:
        try:
            snippet = Snippet.objects.get(snippet=diff['data'][:-1])
            diff['id'] = snippet.id
            diff['level'] = snippet.level
            diff['is_db'] = True
        except Snippet.DoesNotExist:
            diff['level'] = 100
            diff['is_db'] = False

    return render(request, 'compare.html', {'diffs': diffs})
