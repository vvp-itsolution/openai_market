# coding: utf-8
from django.db import models


class MailImage(models.Model):
    name = models.CharField(max_length=120, default='')
    image = models.ImageField(upload_to='app_email/images/')

    class Meta:
        app_label = 'app_email'

    def __unicode__(self):
        return self.name

    __str__ = __unicode__

    def as_base64(self, width, height, crop='center', quality=100, format="JPEG"):
        from PIL import Image, ImageOps
        from io import BytesIO
        import base64

        im = Image.open(self.image.path)
        im = ImageOps.fit(im, (width, height), Image.ANTIALIAS, 0, self._get_crop(crop))

        bytes_io = BytesIO()
        im.save(bytes_io, format=format, quality=quality)

        return base64.b64encode(bytes_io.getvalue())

    @staticmethod
    def _get_crop(pos):
        if pos == 'center':
            return 0.5, 0.5

        elif pos == 'top':
            return 0.0, 0.5

        elif pos == 'bottom':
            return 1.0, 0.5

        elif pos == 'left':
            return 0.5, 0.0

        elif pos == 'right':
            return 0.5, 1.0

    def get_preview_url(self, width, height, crop=None, quality=None, format=None):
        from django.conf import settings

        if not crop:
            crop = 'center'

        if not quality:
            quality = 100

        if not format:
            format = "JPEG"

        return 'https://{domain}/its/img_preview/?' \
               'image={path}&size={width}x{height}&crop={crop}&quality={quality}&format={format}'.format(
            domain=settings.DOMAIN,
            path=self.image.url,
            width=width,
            height=height,
            crop=crop,
            quality=quality,
            format=format
        )
