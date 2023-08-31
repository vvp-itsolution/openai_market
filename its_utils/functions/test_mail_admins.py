#coding: utf-8

'''using
1) start django console

2)
from its_utils.functions.test_mail_admins import test_mail_admins
test_mail_admins()
'''

from django.core.mail import mail_admins

def test_mail_admins():
    mail_admins("test subject", "test message", fail_silently=False)