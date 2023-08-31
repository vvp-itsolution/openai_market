# -*- coding: UTF-8 -*-

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from its_utils.app_documentation.models import Article
from its_utils.app_get_params import get_params_from_sources


@staff_member_required
@get_params_from_sources
def article_get_raw(request):

    try:
        article = Article.objects.get(pk=request.its_params.get('id'))
    except Article.DoesNotExist:
        return HttpResponse('Bad article id', status=400)

    return HttpResponse(article.body)
