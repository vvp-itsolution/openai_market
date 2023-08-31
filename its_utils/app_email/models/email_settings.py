# -*- coding: UTF-8 -*-
from django.core.mail import get_connection

from django.db import models


class EmailSettings(models.Model):
    host = models.CharField(max_length=255, default='')
    port = models.IntegerField(null=True, default=587, blank=True)
    username = models.CharField(max_length=255, default='', blank=True)
    password = models.CharField(max_length=255, default='', blank=True)
    use_tls = models.BooleanField(default=False)
    use_ssl = models.BooleanField(default=False)

    sender_email = models.CharField(max_length=255, default='')

    class Meta:
        app_label = 'app_email'

    def __unicode__(self):
        return u"%s: %s" % (self.host, self.sender_email)

    __str__ = __unicode__

    def get_connection(self):
        return get_connection(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            use_tls=self.use_tls,
            use_ssl=self.use_ssl
        )
