# coding: utf-8
import hashlib

from django.conf import settings
from django.core.mail import send_mail
from django.db import models
try:
    from  django.db.models import JSONField
except:
    from django.contrib.postgres.fields import JSONField
from django.utils import timezone


class TemplatedOutgoingMail(models.Model):
    template = models.ForeignKey('app_email.MailTemplate', on_delete=models.PROTECT)
    from_email = models.ForeignKey('app_email.EmailSettings', on_delete=models.PROTECT)
    to_email = models.TextField(default='')
    params = JSONField(default=dict, blank=True)

    hash = models.CharField(max_length=100, default='', blank=True)

    date_create = models.DateTimeField(default=timezone.now, null=True, blank=True)
    date_sent = models.DateTimeField(null=True, blank=True)

    read = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'app_email'

    def __unicode__(self):
        return u'"{}" to {}'.format(self.template, self.to_email)

    __str__ = __unicode__

    def send_template(self):
        from django.template import Context, Template

        self.hash = self.get_hash()
        self.date_sent = timezone.now()
        self.save()

        context = Context(self.get_params())
        text_content = Template(self.template.text).render(context)
        html_content = u'{}<img src="https://{}/its/marktom/{}_{}.png"></img>'.format(
            Template(self.template.html).render(context), settings.DOMAIN, self.id, self.hash
        )
        subject = Template(self.template.subject).render(context)
        from_email, to_email = self.from_email.sender_email, self.to_email

        return send_mail(subject=subject,
                         message=text_content,
                         from_email=self.from_email.sender_email,
                         recipient_list=[to_email],
                         html_message=html_content,
                         connection=self.from_email.get_connection())

    def get_hash(self):
        return hashlib.md5(u'tom_{}_{}'.format(self.id, self.template.html).encode('utf-8')).hexdigest()

    def get_params(self):
        from its_utils.app_email.models import MailImage
        import re

        params = self.params
        for key, value in self.params.items():
            # Значения вида "app_email_image_{id}_200x200_center_100_JPEG" меняем на ссылку
            # /its/img_preview/image={path}&size=200x200&crop=center&quality=100&format=JPEG
            # Параметры crop, quality, format - необязательные

            pattern = "app_email_image_([0-9]+)_([0-9]+)x([0-9]+)(_([a-z]+))?(_([0-9]+))?(_([A-Z]+))?"
            match = re.match(pattern, value)
            if match:
                mi_id, width, height, _, crop, _, quality, _, format = match.groups()
                try:
                    mi = MailImage.objects.get(id=int(mi_id))
                    params[key] = mi.get_preview_url(width, height, crop, quality, format)

                except MailImage.DoesNotExist:
                    pass

        return params
