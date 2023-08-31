import threading

cron_thread_local = threading.local()


def append_cron_result(text):
    if getattr(cron_thread_local, 'cron_result', None):
        cron_thread_local.cron_result.append_text(text)

