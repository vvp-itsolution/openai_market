from django.db import models
from django.utils import timezone
from django.contrib import admin

from bitrix_utils.bitrix_auth.models import BitrixUserToken
from its_utils.app_admin.action_admin import ActionAdmin


class AbsPortalSettings(models.Model):
    APPLICATION_NAME = None

    portal = models.OneToOneField('bitrix_auth.BitrixPortal', related_name='portal_settings', on_delete=models.PROTECT)
    payment_expired = models.DateField(null=True, blank=True, default=timezone.now)
    data = models.JSONField(default=dict)
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    def get_bx_token(self):
        # type: () -> BitrixUserToken

        return BitrixUserToken.get_random_token(
            application_name=self.APPLICATION_NAME,
            portal_id=self.portal_id,
        )

    class Admin(ActionAdmin):
        raw_id_fields = ['portal']
        pass

    def __str__(self):
        return self.portal.domain

    def is_expired(self):
        return self.trial_date and self.trial_date < timezone.now().date()

    @classmethod
    def by_portal(cls, portal):
        ps, _ = cls.objects.get_or_create(portal_id=portal.id)
        return ps
