# -*- coding: UTF-8 -*-

from django.db import models
from django.utils.encoding import smart_text


class Category(models.Model):

    name = models.CharField(max_length=255)

    class Meta:
        app_label = 'app_documentation'

    def __unicode__(self):
        return smart_text(self.name)
