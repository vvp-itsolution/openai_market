# coding: utf-8
from django.db import models


class MailTemplate(models.Model):
    subject = models.CharField(max_length=255, default='')
    html = models.TextField(default='', blank=True)
    text = models.TextField(default='', blank=True)

    class Meta:
        app_label = 'app_email'

    def __unicode__(self):
        return self.subject

    __str__ = __unicode__