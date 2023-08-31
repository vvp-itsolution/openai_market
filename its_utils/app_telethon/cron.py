import threading
from typing import Type

from django.utils.module_loading import import_string

from its_utils.app_telethon.models import BaseSession


def load_history(class_path):
    session_model = import_string(class_path)  # type: Type[BaseSession]
    session_qs = session_model.objects.filter(is_deleted=False, user__isnull=False)

    results = []
    for session in session_qs:  # type: BaseSession
        result = session.load_history()
        results.append('{}: {}'.format(session, result))

    return '\n'.join(results)
