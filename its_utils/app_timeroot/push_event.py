import threading

import requests
from django.conf import settings


def push_timeroot_event_async(
        user_email,
        event_type,
        hook=None,
        started=None,
        description=None,
        external_url=None):
    threading.Thread(target=push_timeroot_event,
                     args=[user_email, event_type],
                     kwargs={
                         'hook': hook,
                         'started': started,
                         'description': description,
                         'external_url': external_url,
                     }).start()
    return


def push_timeroot_event(
        user_email,
        event_type,
        hook=None,
        started=None,
        description=None,
        external_url=None
):

    if not hook:
        hook = settings.TIMEROOT_HOOK

    data = dict(
        hook=hook,
        userEmail=user_email,
        type=event_type,
        started=started,
        description=description,
        externalUrl=external_url
    )

    return requests.post("https://timeroot.ru/api/event/create/", data=data)


