from django.db import models
from bitrix_utils.bitrix_auth.models.abs_portal_settings import AbsPortalSettings


class PortalSettingsGptConnector(AbsPortalSettings):
    # Может быть несколкьо приложений в одном репозитории, поэтому лучше использовать суффикс к приложению
    # PortalSettings + GptProxy
    gpt_api_key = models.CharField(blank=True, null=True, max_length=64)
