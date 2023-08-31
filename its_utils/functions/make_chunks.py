# coding: utf-8


def make_chunks(lst, size):
    """
    Генератор подсписков по n элементов
    """

    for i in range(0, len(lst), size):
        yield lst[i:i + size]
