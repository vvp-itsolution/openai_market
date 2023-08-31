# coding=UTF-8
from django.db import models


class BitrixOpenLine(models.Model):
    name = models.CharField(verbose_name='Название', max_length=500)
    bx_id = models.CharField(verbose_name='ID', max_length=500)

    def __unicode__(self):
        return str(self.name)

    __str__ = __unicode__
