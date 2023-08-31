# -*- coding: UTF-8 -*-

import difflib

from django.db import models
from django.contrib.auth.models import User
from django.db.models.deletion import PROTECT


class Diff(models.Model):
    user = models.ForeignKey(User, on_delete=PROTECT)
    article = models.ForeignKey('Article', editable=False, on_delete=PROTECT)
    data = models.TextField(editable=False)
    body = models.TextField(editable=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'app_documentation'

    @classmethod
    def add_new_and_get_diff(cls, user, article, old_body, body):
        # body = body.decode('utf8').splitlines()
        new_article_body = body
        body = body.splitlines()
        old_body = old_body.splitlines()

        data = ''.join(difflib.unified_diff(old_body, body))

        cls(user=user, article=article, body=new_article_body, data=data).save()
        return data

    def __unicode__(self):
        return '%s' % self.article
