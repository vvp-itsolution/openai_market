import threading

from settings import ilogger

_marker = threading.local()


def put(label, text):
    if not hasattr(_marker, label):
        setattr(_marker, label, [])

    markers = getattr(_marker, label, None)
    markers.append(text)

    if len(markers) >= 100:
        ilogger.warning('marker', 'Возможно не очищается!!')

    return markers


def list(label):
    return getattr(_marker, label, [])
