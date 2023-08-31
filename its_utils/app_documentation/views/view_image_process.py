# -*- coding: UTF-8 -*-

import json

from django.http import HttpResponse
from django.shortcuts import redirect
#from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

from its_utils.app_documentation.models import Article, Image


@csrf_exempt
@staff_member_required
def view_image_process(request):
    if request.method == 'POST':
        article_id, image_file = list(request.FILES.items())[0]

        article = Article.objects.get(pk=article_id)
        image = Image(article=article, image=image_file)

        image.save()

        data = {
            'pk': image.pk,
            'url': image.image.url
        }

        return HttpResponse(json.dumps(data))

    if request.method == 'DELETE':
        pk = request.GET.get('pk', None)

        if pk:
            Image.objects.get(pk=pk).delete()
            return HttpResponse('', status=204)

    return redirect(reverse('article_list'))
