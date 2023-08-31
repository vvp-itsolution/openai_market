# -*- coding: UTF-8 -*-

import json

from django.http import HttpResponse
from django.db import IntegrityError
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
#from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View


from its_utils.app_documentation.models import Article, Image, Directory

from django.utils.decorators import method_decorator


@csrf_exempt
def view_get_article_render(request):
    if request.method == 'POST':
        render = Article.render(json.loads(request.body)['body'])
        return HttpResponse(render)
    else:
        return HttpResponse('Only post')


@csrf_exempt
def view_change_article_dir(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        article_pk = data['articlePk']
        dir_pk = data['dirPk']

        article = Article.objects.get(pk=article_pk)
        directory = Directory.objects.get(pk=dir_pk)
        article.directory = directory
        article.save()
        return HttpResponse(directory.name)
    else:
        return HttpResponse('Post only')


class ArticleEdit(View):

    template = 'documentation/article_edit.html'

    @method_decorator(csrf_exempt)
    def dispatch(self, request, pk=None):

        if pk:
            self.article = Article.objects.get(pk=pk)
            self.images = Image.objects.filter(article=self.article).order_by('-id')
        else:
            self.article = Article()
            self.images = []

        directories = [(d['pk'], '-' * d['level'] + d['name'])
                       for d in Directory.objects.values('pk', 'level', 'name')]

        self.context = {'article': self.article,
                        'images': self.images,
                        'directories': directories,
                        }

        return super(self.__class__, self).dispatch(request, pk)

    @method_decorator(staff_member_required)
    def get(self, request, pk=None):

        return render(request, self.template, self.context)

    @method_decorator(staff_member_required)
    def post(self, request, pk):

        self.article.user = request.user
        self.article.title = request.POST.get('title', '')
        self.article.body = request.POST.get('body', '')

        try:
            self.article.save()
        except IntegrityError:
            self.context['error'] = 'Статья с таким именем уже существует'
            self.article.pk = ''
            return render(request, self.template, self.context)
        else:
            return redirect(reverse('article', args=[self.article.pk]))

    @method_decorator(staff_member_required)
    def delete(self, request, pk):

        self.article.deleted = True
        self.article.save()

        return HttpResponse('Ok')
