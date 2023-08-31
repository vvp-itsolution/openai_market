# coding=utf8

from django.db import models


class AssetsAbstract(models.Model):
    name = models.CharField(u'Название', max_length=200, blank=True)
    created = models.DateTimeField(u'Создано', auto_now_add=True)
    updated = models.DateTimeField(u'Последнее обновление', auto_now=True)

    class Meta:
        abstract = True
