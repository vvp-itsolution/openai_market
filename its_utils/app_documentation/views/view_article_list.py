# -*- coding: UTF-8 -*-

from django.shortcuts import render
# from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

from its_utils.app_documentation.models import Article


# @csrf_exempt
@staff_member_required
def view_article_list(request):
    articles = Article.objects.filter(deleted=False)
    context = {'articles': articles}
    return render(request, 'documentation/article_list.html', context)
