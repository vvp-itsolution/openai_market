# coding=UTF-8
from django.db import models

from its_utils.functions.compatibility import get_null_boolean_field

NullBooleanField = get_null_boolean_field()


class BitrixApp(models.Model):
    name = models.CharField(max_length=100)
    bitrix_client_id = models.CharField(max_length=100)
    bitrix_client_secret = models.CharField(max_length=100)
    scope = models.CharField(max_length=500, null=True)
    redirect_url = models.CharField(max_length=500, null=True)
    domain = models.CharField(max_length=500, null=True)

    # это webhook
    is_webhook = NullBooleanField(default=False, null=True)

    # просто описание, дабы понимать, что это за приложение и с какой целью создано
    description = models.CharField(max_length=500, null=True, blank=True)

    def __unicode__(self):
        return self.name

    __str__ = __unicode__
