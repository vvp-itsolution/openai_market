# coding=utf-8

from __future__ import unicode_literals

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class ObjectHistory(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name='Тип объекта')
    object_id = models.PositiveIntegerField(verbose_name='id объекта')
    content_object = GenericForeignKey('content_type', 'object_id')

    time = models.DateTimeField(default=timezone.now, verbose_name='Время')
    message = models.TextField(default='', blank=True, verbose_name='Сообщение')

    class Meta:
        app_label = 'app_object_history'
        verbose_name = u'Запись истории объекта'
        verbose_name_plural = u'История объектов'

    @classmethod
    def new_record(cls, obj, message):
        return cls.objects.create(content_object=obj, message=message)
