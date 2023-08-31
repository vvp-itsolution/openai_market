# -*- coding: UTF-8 -*-
from __future__ import unicode_literals

import re

from django.core.mail import EmailMultiAlternatives

from django.db import models


class OutgoingEmail(models.Model):
    # soe = suffix outgoing email

    sender_soe = models.CharField(max_length=255)
    from_soe = models.CharField(max_length=255)
    to_soe = models.CharField(max_length=255)
    cc_soe = models.CharField(max_length=255, blank=True, null=True)
    bcc_soe = models.CharField(max_length=255, blank=True, null=True)
    subject_soe = models.CharField(max_length=255)
    text_content_soe = models.TextField()
    html_content_soe = models.TextField()

    is_sent_soe = models.BooleanField(default=False, db_index=True)

    #     MIME-Version: 1.0
    # Sender: hlopikit@gmail.com
    # Received: by 10.25.157.3 with HTTP; Mon, 13 Jun 2016 12:13:26 -0700 (PDT)
    # Bcc: =?UTF-8?B?0KHQtdGA0LPQtdC5INCa0L7Qt9C70L7Qsg==?= <ksk@it-solution.ru>
    # Date: Mon, 13 Jun 2016 22:13:26 +0300
    # Delivered-To: hlopikit@gmail.com
    # X-Google-Sender-Auth: xyE7KpEZmOojPTDQj3CF7TxjwSI
    # Message-ID: <CABqkhjW0UfcKcujKhti2qUFtiJinVgmgi5SPk89y95y2pFJ-Bg@mail.gmail.com>
    # Subject: =?UTF-8?B?0KLQtdGB0YI=?=
    # From: =?UTF-8?B?0JXQstCz0LXQvdC40Lkg0KXQu9C+0LHRi9GB0YLQuNC9?= <evg@it-solution.ru>
    # To: "evg@it-solution.ru" <evg@it-solution.ru>
    # Cc: bav@it-solution.ru

    def send(self):
        """
        :admin_action_description: Отправить письмо
        """
        from its_utils.app_email.models import EmailSettings

        # Если в таблице EmailSettings есть запись с отправителем, будем использовать авторизацию
        connection = None
        settings = EmailSettings.objects.filter(sender_email=self.sender_soe).last()
        if settings:
            connection = settings.get_connection()

        subject, from_email = self.subject_soe, self.from_soe

        to = re.split('[;,]', self.to_soe)
        cc = re.split('[;,]', self.cc_soe)
        bcc = re.split('[;,]', self.bcc_soe) if self.bcc_soe else None

        text_content = self.text_content_soe
        html_content = self.html_content_soe

        msg = EmailMultiAlternatives(subject, text_content, from_email, to, cc=cc, bcc=bcc, connection=connection)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        # mail_templated.send_mail('mail/ticket_new.html',
        #                              context=locals(),
        #                              from_email='ts@it-solution.ru',
        #                              recipient_list=[email])
        self.is_sent_soe = True
        self.save()

    def to_string(self):
        return u'\n'.join([u'От: {self.from_soe}',
                           u'Отправитель: {self.sender_soe}',
                           u'Получатель: {self.to_soe},',
                           u'Тема: {self.subject_soe}']).format(self=self)

    class Meta:
        app_label = 'app_email'

    def __unicode__(self):
        return u'{self.id}. {self.to_soe}: {self.subject_soe}'.format(self=self)

    __str__ = __unicode__
