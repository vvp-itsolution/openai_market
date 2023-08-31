# coding=UTF-8
from django.db import models
from django.utils import timezone
from bitrix_utils.bitrix_auth.models import BitrixUserToken
from bitrix_utils.bitrix_auth.models.bitrix_user_token import BitrixApiError, BitrixTimeout
from its_utils.app_admin.action_admin import ActionAdmin
from requests.exceptions import ConnectTimeout
from urllib3.exceptions import MaxRetryError


class BitrixNotification(models.Model):
    Notification_Types = (
        (0, 'Уведомление'),
        (1, 'Открытая линия'),
    )

    EXPECTED_ERRORS = (
        BitrixApiError,
        ConnectTimeout,
        MaxRetryError,
        BitrixTimeout
    )

    application = models.ForeignKey('bitrix_auth.BitrixApp', on_delete=models.CASCADE)
    user = models.ForeignKey('bitrix_auth.BitrixUser', related_name='bitrix_notification', on_delete=models.CASCADE)
    type = models.PositiveSmallIntegerField(choices=Notification_Types, default=0)
    message = models.TextField(default='')
    date_sent = models.DateTimeField(null=True, blank=True)
    sent = models.BooleanField(default=False)
    error = models.BooleanField(default=False)
    error_text = models.TextField(null=True, blank=True)
    open_line = models.ForeignKey('bitrix_auth.BitrixOpenLine', on_delete=models.PROTECT, null=True, blank=True,
                                  help_text='только если тип = открытая линия')

    class Admin(ActionAdmin):
        list_display = ('id', 'application', 'user', 'type', 'message', 'date_sent', 'sent', 'error', 'open_line')
        list_display_links = list_display
        search_fields = 'user__id', 'user__first_name', 'user__last_name', 'user__portal__domain', 'message'
        list_filter = ['application', 'sent', 'error', 'open_line', 'date_sent', 'type']
        raw_id_fields = ['user']

        actions = ["send"]

    def __unicode__(self):
        return str(self.user) + ' "' + self.message[0:15] + '"'

    __str__ = __unicode__

    def send(self):
        """
        :admin_action_description: Отправить уведомление
        """
        if self.type == 1 and not self.open_line:
            return 'НЕ ОТПРАВЛЕНО — не указана открытая линия'

        bx_token = None

        if self.type == 1:
            # для уведомления через открытую линию нужен токен именно того пользователя, который будет получателем сообщения
            user_token_query = BitrixUserToken.objects.filter(
                application=self.application, user=self.user, is_active=True
            )
            if user_token_query.count():
                bx_token = user_token_query.last()
        else:
            # для обычного уведомления (в колокольчик) подойдет токен администратора и, возможно, в худшем случае любого пользователя на портале
            admin_token_query = BitrixUserToken.objects.filter(
                application=self.application, user__portal__domain=self.user.portal.domain, user__is_admin=True, is_active=True
            )
            if admin_token_query.count():
                bx_token = admin_token_query.last()
            else:
                any_token_query = BitrixUserToken.objects.filter(
                    application=self.application, user__portal__domain=self.user.portal.domain, is_active=True
                )
                if any_token_query.count():
                    bx_token = any_token_query.last()

        error_text = ''

        if bx_token:
            try:
                if self.type == 1:
                    # пишем через открытую линию
                    response = None

                    line_join_response = bx_token.call_api_method('imopenlines.network.join', {
                        'CODE': self.open_line.bx_id
                    })
                    if line_join_response and 'result' in line_join_response and line_join_response['result']:
                        response = bx_token.call_api_method('imopenlines.network.message.add', {
                            'CODE': self.open_line.bx_id,
                            'USER_ID': self.user.bitrix_id,
                            'MESSAGE': self.message
                        })
                else:
                    # пишем через уведомление (колокольчик)
                    response = bx_token.call_api_method('im.notify', {
                        'to': self.user.bitrix_id,
                        'message': self.message,
                        'type': 'SYSTEM'
                    }, timeout=5)

                if response and 'result' in response and response['result']:
                    self.date_sent = timezone.now()
                    self.sent = True
                    self.save()
                    return True
                else:
                    error_text = 'НЕ ОТПРАВЛЕНО — bitrix response = ' + str(response)
            except self.EXPECTED_ERRORS as e:
                error_text = 'НЕ ОТПРАВЛЕНО — BitrixApiError = ' + str(e)
        else:
            error_text = 'НЕ ОТПРАВЛЕНО — Нет подходящего BitrixUserToken'

        if error_text:
            self.error = True
            self.error_text = error_text
            self.save()
        else:
            error_text = 'НЕ ОТПРАВЛЕНО'

        return False

    @classmethod
    def send_all(cls, limit=300):
        import concurrent.futures
        sent = error = 0

        notifications = cls.objects.filter(sent=False, error=False)[0:limit]
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            future_notify = [executor.submit(notification.send) for notification in notifications]
            result = concurrent.futures.as_completed(future_notify)
            for r in result:
                if r.result():
                    sent += 1
                else:
                    error += 1
        return sent, error


def send_all_cron():
    return BitrixNotification.send_all()
