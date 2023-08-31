# -*- coding: UTF-8 -*-

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from its_utils.app_documentation.models import Article
from its_utils.app_get_params import get_params_from_sources


@csrf_exempt
@staff_member_required
@get_params_from_sources
def article_save(request):

    try:
        article = Article.objects.get(pk=request.its_params.get('id'))
    except Article.DoesNotExist:
        return HttpResponse('Bad article id', status=400)

    try:
        article.body = request.its_params['body']
    except KeyError:
        return HttpResponse('Need "body" parameter', status=400)

    article.save()
    return HttpResponse(article.rendered_body)
