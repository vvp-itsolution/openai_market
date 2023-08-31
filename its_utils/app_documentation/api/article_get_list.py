# -*- coding: UTF-8 -*-

import json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from its_utils.app_documentation.models import Article


@staff_member_required
def article_get_list(request):
    articles = list(Article.objects.values('id', 'title'))
    return HttpResponse(json.dumps(articles))
