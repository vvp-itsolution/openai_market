# -*- coding: utf-8 -*-
__author__ = 'andrew'


def file_get_content(file_path, offset=None, maxlen=None):
    """
        Читает содержимое файла в строку

        :param file_path: str
        :param offset: int
        :param maxlen: int
        :return: bool | str
    """

    # Если параметр не типа int
    if offset is not None and type(offset) != int:
        # Возвращаем False
        return False

    # Если параметр не типа int
    if maxlen is not None and type(maxlen) != int:
        # Возвращаем False
        return False

    # Пытаемся открыть файл
    try:
        f = open(file_path)
        # Если задано смещение
        if offset:
            # Смещаемся на указанное количество байт
            f.seek(offset)
        # Если задан максимальный размер данных
        if maxlen:
            # Берем тольк заданное количество
            content = f.read(maxlen)
        # В противном случае берем все содержимое
        else:
            content = f.read()
    except:
        # Если произошла ошибка возвращаем False
        return False
    else:
        # Если чтение прошо успешно,
        # то возвращаем содержимое
        return content


if __name__ == '__main__':
    print('all file content')
    print(file_get_content('__init__.py'))
    print('----------------------------------------')
    print('content from 2 byte')
    print(file_get_content('__init__.py', 2))
    print('----------------------------------------')
    print('content from 2 to 6 byte')
    print(file_get_content('__init__.py', 2, 6))
    print('----------------------------------------')
    print('wrong params')
    print(file_get_content('_init_.py'))
    print(file_get_content('__init__.py', '3'))
    print(file_get_content('__init__.py', '3', '3'))
