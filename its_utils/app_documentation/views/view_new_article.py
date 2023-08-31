# -*- coding: UTF-8 -*-


from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required

from its_utils.app_documentation.models import Article


@staff_member_required
def view_new_article(request, article_id=None):
    if request.method == 'POST':
        title = request.POST['title']
        body = request.POST['body']
        user = request.user

        article = Article(title=title, body=body, user=user)
        article.save()
        return redirect('/article/%s/' % article.slug)

    return render(request, 'documentation/new_article.html', {})
