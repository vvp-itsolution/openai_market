import threading
import time

__logger_thread_local = threading.local()


def set_request_start_time():
    setattr(__logger_thread_local, 'request_start_time', time.time())


def get_request_start_time():
    return getattr(__logger_thread_local, 'request_start_time', 'unknown')
