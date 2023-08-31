# coding=utf8
from django.db import models
from its_utils.app_assets.functions import get_upload_to
from its_utils.app_assets.models import AssetsAbstract


class AssetsFile(AssetsAbstract):
    file = models.FileField(u'Файл', upload_to=get_upload_to('files'))

    def __unicode__(self):
        return u'%s %s %s' % (self.pk, self.name,
                              self.file.name if self.file else u'<пусто>')

    __str__ = __unicode__

    class Meta:
        verbose_name = u'файл'
        verbose_name_plural = u'файлы'
