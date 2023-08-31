# -*- coding: UTF-8 -*-

from django.db import models


class Application(models.Model):

    name = models.CharField(max_length=255)

    class Meta:
        app_label = 'app_release'

    def __unicode__(self):
        return self.name

    def __str__(self):
        return '{} (id={})'.format(self.name, self.id)
