# -*- coding: UTF-8 -*-

from django.shortcuts import render, redirect
#from django.core.urlresolvers import reverse
from django.db.models import Q


from its_utils.app_documentation.models import Article

def view_article_search(request):
    if request.POST:
        query = request.POST.get('query', '')
        if query:
            articles = Article.objects.filter(Q(body__icontains=query) | Q(title__icontains=query))

            template = 'documentation/article_search.html'
            context = {'articles': articles,
                       'query': query}

            return render(request, template, context)

    return redirect(reverse('article_list'))
