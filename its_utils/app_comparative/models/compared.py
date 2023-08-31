# coding: utf-8
import requests
from django.db import models

from its_utils.app_comparative.functions.diff import text_diff


class Compared(models.Model):
    url1 = models.URLField(u'Url 1', max_length=255)
    url2 = models.URLField(u'Url 2', max_length=255)

    last_compare = models.CharField(max_length=255, default='')

    def compare(self):
        page1 = requests.get(self.url1).content.decode('utf-8')
        page2 = requests.get(self.url2)# .content.decode('utf-8')

        if page2.status_code == 200:
            page2 = page2.content.decode('utf-8')
            res = text_diff(page1, page2)
            return res
        else:
            return None

    def check_compare(self):
        from its_utils.app_comparative.models import Snippet
        diffs = self.compare()

        if diffs is None:
            self.last_compare = 'Status code is not 200'
            self.save()
            return

        res = {}

        for diff in diffs:
            try:
                snippet_level = Snippet.objects.get(snippet=diff['data'][:-1]).level
            except Snippet.DoesNotExist:
                snippet_level = 100

            if res.get(snippet_level, 0):
                res[snippet_level] += 1
            else:
                res[snippet_level] = 1

            self.last_compare = "100:%s / 30:%s / 20:%s / 10:%s" % (res.get(100, 0), res.get(30, 0), res.get(20, 0), res.get(10, 0))
            self.save()

    def __unicode__(self):
        return self.url1
