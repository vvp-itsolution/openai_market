import openai
import requests

from django.db import models
from django.utils import timezone

from bitrix_utils.bitrix_auth.models import BitrixPortal
from bitrix_utils.bitrix_auth.models.abs_portal_settings import AbsPortalSettings
from gptconnector.models import PortalSettingsGptConnector
from its_utils.app_admin.action_admin import ActionAdmin


class AiTask(models.Model):
    portal = models.ForeignKey(
        BitrixPortal,
        on_delete=models.CASCADE,
        help_text='Портал с которого был выполнен запрос'
    )
    prompt = models.TextField(
        help_text='Ваш запрос'
    )
    response_content = models.TextField(
        null=True,
        blank=True,
        help_text='Ответ GPT'
    )
    created = models.DateTimeField(
        default=timezone.now,
        help_text='Время создания запроса'
    )
    callback_url = models.URLField()
    is_processed = models.BooleanField(
        default=False,
        db_index=True,
    )
    processed_dt = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Время, в которое запрос был выполнен"
    )
    prompt_tokens = models.IntegerField(
        null=True,
        blank=True,
        help_text="Количество израсходованных токенов на запрос"
    )
    completion_tokens = models.IntegerField(
        null=True,
        blank=True,
        help_text="Количество израсходованных токенов на ответ"
    )

    class Admin(ActionAdmin):
        list_display = ['prompt', 'portal', 'is_processed', 'processed_dt', 'prompt_tokens', 'completion_tokens']
        raw_id_fields = ['portal']
        actions = ["process"]

    def process(self):
        """
        :admin_action_description: Обработать запрос
        """


        # by_portal используется как альтернатива self.portal.portal_settings_gpt_connector.gpt_api_key релайтед запись, она вглядит менее удобно
        openai.api_key = PortalSettingsGptConnector.by_portal(self.portal).gpt_api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{'role': 'user', 'content': self.prompt}]
        )
        response_content = response.choices[0].message.content
        requests.post(self.callback_url, json={"result": [response_content]})
        self.response_content = response_content
        self.processed_dt = timezone.now()
        self.is_processed = True
        self.prompt_tokens = response['usage']['prompt_tokens']
        self.completion_tokens = response['usage']['completion_tokens']
        self.save()

    @classmethod
    def process_all(cls):
        for task in AiTask.objects.filter(is_processed=False):
            task.process()
