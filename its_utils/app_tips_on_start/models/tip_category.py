# -*- coding: utf-8 -*-
import six
from django.contrib import admin
from django.db import models


@six.python_2_unicode_compatible
class TipCategory(models.Model):
    title = models.CharField(u'название', max_length=255, unique=True)

    class Meta:
        verbose_name = 'категория подсказки'
        verbose_name_plural = 'категории подсказок'

    def __str__(self):
        return u'{self.title}'.format(self=self)

    class Admin(admin.ModelAdmin):
        list_display = 'id', 'title',
        list_display_links = list_display
        search_fields = 'id', 'title',
