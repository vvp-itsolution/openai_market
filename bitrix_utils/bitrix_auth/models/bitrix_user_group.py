# -*- coding: UTF-8 -*-

from django.db import models


class BitrixUserGroup(models.Model):

    user = models.ForeignKey('bitrix_auth.BitrixUser', on_delete=models.CASCADE)
    group = models.ForeignKey('bitrix_auth.BitrixGroup', on_delete=models.CASCADE)

    class Meta:
        app_label = 'bitrix_auth'

    def __unicode__(self):
        return u'%s %s' % (self.group, self.user)
