# -*- coding: UTF-8 -*-

from django.http import HttpResponse
from django.shortcuts import render

from its_utils.app_documentation.models import Article


def article_read(request, pk):

    try:
        article = Article.objects.get(pk=pk, secret_key=request.GET.get('key', None))
    except Article.DoesNotExist:
        return HttpResponse('404: Article was not found', status=404)

    template = 'documentation/article_read.html'
    context = {
        'article': article
    }

    return render(request, template, context)
