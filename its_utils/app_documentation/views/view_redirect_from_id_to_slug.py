# -*- coding: UTF-8 -*-

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

from its_utils.app_documentation.models import Article


@staff_member_required
def view_redirect_from_id_to_slug(requset, article_id):
    article = get_object_or_404(Article, id=article_id)
    return HttpResponse(article)
    # print(article)
