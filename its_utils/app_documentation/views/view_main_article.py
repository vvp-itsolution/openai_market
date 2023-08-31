# -*- coding: UTF-8 -*-

# from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
#from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist

from its_utils.app_documentation.models import Article, Directory
from its_utils.app_documentation.documentation_settings import ITS_UTILS_DOCUMENTATION


@staff_member_required
def view_main_article(request):
    main_article = ITS_UTILS_DOCUMENTATION.get('MAIN_ARTICLE', None)

    try:
        article = Article.objects.get(slug=main_article)
    except ObjectDoesNotExist:
        return redirect(reverse('article_list'))

    article.title = ITS_UTILS_DOCUMENTATION.get('MAIN_ARTICLE_TITLE', '')
    directories = Directory.objects.all()

    context = {
        'article': article,
        'directories': directories,
    }

    return render(request, 'documentation/article.html', context)
