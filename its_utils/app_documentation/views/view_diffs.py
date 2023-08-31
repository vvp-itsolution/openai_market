# -*- coding: UTF-8 -*-

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from its_utils.app_documentation.models import Diff


@staff_member_required
def view_diffs(request, pk=None):
    if pk:
        diffs = Diff.objects.filter(article__pk=pk).order_by('-created')
    else:
        diffs = Diff.objects.all().order_by('-created')[:10]

    context = {'diffs': diffs}
    return render(request, 'documentation/diffs.html', context)
