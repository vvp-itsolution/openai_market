# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from django.utils.html import format_html

from bitrix_utils.bitrix_auth.models import BitrixUserToken


class BitrixAppInstallation(models.Model):
    portal = models.ForeignKey('bitrix_auth.BitrixPortal', on_delete=models.CASCADE)
    application = models.ForeignKey('bitrix_auth.BitrixApp', on_delete=models.CASCADE)
    installation_date = models.DateTimeField(default=timezone.now)

    # Токен, передающийся в онлайн-события, уникален в рамках portal+app
    application_token = models.CharField(max_length=256, null=True, blank=True)

    # идентификатор установленного приложения на портале пользователя (локально)
    app_id = models.IntegerField(null=True)

    class Meta:
        unique_together = ('portal', 'application')

    def is_active(self):
        """
        :return: True, если есть хоть один действующий токен, иначе False
        """

        tokens = BitrixUserToken.objects.filter(user__portal=self.portal,
                                                application=self.application,
                                                is_active=True)

        return tokens.exists()

    def get_token(self):
        """
        :return: Возвратит любой действующий токен (BitrixUserToken)
        """

        return BitrixUserToken.objects.filter(user__portal=self.portal,
                                              application=self.application,
                                              is_active=True).first()

    def get_url_to_tokens(self):
        """
        :return: ссылка к BitrixUserToken этой инсталяции
        """

        return format_html(u'<a href="/admin/bitrix_auth/bitrixusertoken/'
                           u'?application__id__exact={}&user__portal__domain={}" target="_blank">Токены</a>'
                           .format(self.application_id, self.portal.domain))

    def get_app_url(self):
        """
        Получить ссылку на установленное приложение
        """
        url = 'https://{}/marketplace/app/{}/'.format(self.portal.domain, self.app_id)
        return url

    get_url_to_tokens.short_description = 'Токены'
