# -*- coding: UTF-8 -*-

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required

from its_utils.app_documentation.models import Directory


@staff_member_required
def article_tree(request):

    directories = Directory.get_dirs_with_articles()

    template = 'documentation/article_tree.html'
    context = {
        'directories': directories,
    }

    return render(request, template, context)
