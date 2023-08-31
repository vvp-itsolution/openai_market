# -*- coding: UTF-8 -*-

from django.shortcuts import get_object_or_404, render
# from django.core.urlresolvers import reverse
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.views.generic import View

from its_utils.app_documentation.models import Article, Diff, Directory


class ArticleView(View):

    @method_decorator(staff_member_required)
    def get(self, request, pk):
        article = get_object_or_404(Article, pk=pk)
        diffs = Diff.objects.filter(article=article).order_by('-created')[:10]
        directories = Directory.get_dirs_with_articles()

        context = {
            'host': request.META['HTTP_HOST'],
            'article': article,
            'diffs': diffs,
            'directories': directories,
        }

        return render(request, 'documentation/article.html', context)


# def view_article(request, pk):
#     article = get_object_or_404(Article, pk=pk)
#     diffs = Diff.objects.filter(article=article).order_by('-created')[:10]

#     context = {
#         'article': article,
#         'diffs': diffs,
#     }

#     return render(request, 'documentation/article.html', context)
