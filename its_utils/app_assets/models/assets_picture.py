# coding=utf8
from django.db import models
from its_utils.app_assets.functions import get_upload_to
from its_utils.app_assets.models import AssetsAbstract


class AssetsPicture(AssetsAbstract):
    picture = models.ImageField(u'Картинка', upload_to=get_upload_to('pictures'))

    def __unicode__(self):
        return u'%s %s %s' % (self.pk, self.name,
                              self.picture.name if self.picture else u'<пусто>')

    __str__ = __unicode__

    class Meta:
        verbose_name = u'картинка'
        verbose_name_plural = u'картинки'
