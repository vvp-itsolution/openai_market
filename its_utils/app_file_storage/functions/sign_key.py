# coding: utf-8

import settings
from django.core.signing import Signer


def sign_key(string_for_sign):
    signer = Signer(settings.FILE_STORAGE_SIGNER_SECRET)
    key = signer.sign(string_for_sign).split(':')[-1]
    return key