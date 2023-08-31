# -*- coding: UTF-8 -*-


from django.db import models
from django.db.models.deletion import PROTECT


class Image(models.Model):

    article = models.ForeignKey('Article', on_delete=PROTECT)
    image = models.ImageField(upload_to='its/docs/images/%Y/%m/%d')

    class Meta:
        app_label = 'app_documentation'

    def image_tag(self):
        return ('<img style="max-width:100%%; max-height:100%%; width:200px;" src="/%s" />'
                % self.image.url)

    image_tag.short_description = 'Image'
    image_tag.allow_tags = True
